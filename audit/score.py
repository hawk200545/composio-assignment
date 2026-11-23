import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_DATA = ROOT / "slides" / "public" / "data"
DIMENSIONS = {
    "Auth": ("auth",),
    "Credential access": ("developer_access", "production_access"),
    "API surface": ("api_interfaces", "api_breadth"),
    "MCP": ("mcp",),
}
FIELD_NAMES = {
    "auth": "Auth",
    "developer_access": "Developer access",
    "production_access": "Production access",
    "api_interfaces": "API interfaces",
    "api_breadth": "API breadth",
    "mcp": "MCP",
}


def load_predictions(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = {row["id"]: row["claims"] for row in data}
    if len(data) != len(rows):
        raise ValueError(f"Duplicate app IDs in {path}")
    return rows


def grade(field, label, claim):
    if claim["conflict"] or not claim["values"]:
        return "abstained"
    aliases = label.get("equivalent_values", {})
    values = {aliases.get(value, value) for value in claim["values"]}
    if field == "mcp" and values == {"official", "community"}:
        values = {"official"}
    return "correct" if values == set(label["expected"]) else "incorrect"


def ratio(numerator, denominator):
    if not denominator:
        return "—"
    return f"{numerator}/{denominator} ({numerator / denominator:.1%})"


def metrics(counts):
    correct = counts["correct"]
    answered = correct + counts["incorrect"]
    total = answered + counts["abstained"]
    return correct, answered, total


def display_claim(claim):
    if claim["conflict"]:
        return "abstained (conflict)"
    return ", ".join(claim["values"]) or "abstained"


def main():
    parser = argparse.ArgumentParser(description="Compare saved passes with frozen holdout labels.")
    parser.add_argument("--run", type=Path, default=PUBLISHED_DATA, help="Directory containing the original run exports")
    parser.add_argument("--labels", type=Path, default=PUBLISHED_DATA / "holdout-labels.json")
    parser.add_argument("--patched-results", type=Path, help="Optional results.json from a verifier replay")
    args = parser.parse_args()
    raw_labels = args.labels.read_bytes()
    labels = json.loads(raw_labels)
    predictions = [load_predictions(args.run / name) for name in ("first-pass.json", "results.json")]
    passes = ("First pass", "Revised")
    if args.patched_results:
        predictions.append(load_predictions(args.patched_results))
        passes = ("First pass", "Original verifier", "Patched verifier")
    sample = json.loads((ROOT / labels["holdout"]).read_text(encoding="utf-8"))["apps"]
    ids = [app["id"] for app in labels["apps"]]
    if ids != [app["id"] for app in sample] or any(not set(ids) <= rows.keys() for rows in predictions):
        raise ValueError("The labels must match the reserved sample and each export must include it.")

    rows = []
    unknown = []
    for app in labels["apps"]:
        if set(app["fields"]) != set(FIELD_NAMES):
            raise ValueError(f"Incomplete field list for {app['name']}")
        for field, label in app["fields"].items():
            expected = label["expected"]
            if expected is None:
                unknown.append((app["name"], FIELD_NAMES[field], label["reason"]))
                continue
            if not expected or not label["sources"]:
                raise ValueError(f"Missing evidence for {app['name']} {field}")
            claims = [prediction[app["id"]][field] for prediction in predictions]
            rows.append({
                "app": app["name"],
                "field": field,
                "expected": ", ".join(expected),
                "claims": tuple(display_claim(claim) for claim in claims),
                "grades": tuple(grade(field, label, claim) for claim in claims),
                "source": label["sources"][0],
            })

    def counts(index, subset=rows):
        return Counter(row["grades"][index] for row in subset)

    print("# Held-out accuracy audit")
    print()
    sample_size = "ten" if len(ids) == 10 else str(len(ids))
    print(f"On {labels['audited_on']}, {sample_size} apps were checked against published primary sources. ", end="")
    if args.patched_results:
        print("The seeded draw excluded the pilot and the original audit. The AI-assisted review "
              "froze its labels before opening the predictions. The patched verifier used the saved "
              "first-pass claims and cached source text from the original run.")
    else:
        print("The sample was chosen before the batch. The AI-assisted manual document review "
              "saved its labels before reading either model pass.")
    print()
    print(
        "An answer is correct when its values match the documented label under the frozen "
        "rubric. An empty answer or unresolved conflict is an "
        "abstention. Accuracy uses all scorable fields. Coverage uses the share answered. "
        "Accuracy on answers uses answered fields as its denominator. "
        f"[Rubric and sources]({args.labels.name})"
    )
    print()
    print("| Pass | Accuracy | Coverage | Accuracy on answers | Incorrect | Abstained |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for index, name in enumerate(passes):
        tally = counts(index)
        correct, answered, total = metrics(tally)
        print(
            f"| {name} | {ratio(correct, total)} | {ratio(answered, total)} | "
            f"{ratio(correct, answered)} | {tally['incorrect']} | {tally['abstained']} |"
        )

    print()
    changes = Counter(row["grades"][-2:] for row in rows)
    fixed = changes["incorrect", "correct"]
    filled = changes["abstained", "correct"]
    regressed = changes["correct", "incorrect"] + changes["correct", "abstained"]
    withheld = changes["incorrect", "abstained"]
    if args.patched_results:
        print(
            f"Against the original verifier, {fixed} fields went from incorrect to correct, "
            f"{filled} from abstained to correct, {regressed} from correct to incorrect or abstained, "
            f"and {withheld} from incorrect to abstained."
        )
    else:
        print(
            f"Verification corrected {fixed} wrong answers and filled {filled} abstentions correctly. "
            f"It lost {regressed} previously correct answers and withdrew {withheld} wrong answers."
        )
    print()
    print("## Accuracy by dimension")
    print()
    pass_columns = " | ".join(passes)
    right_columns = " ---: |" * len(passes)
    print(f"| Dimension | {pass_columns} |")
    print(f"| --- |{right_columns}")
    for dimension, fields in DIMENSIONS.items():
        subset = [row for row in rows if row["field"] in fields]
        ratings = [metrics(counts(index, subset)) for index in range(len(passes))]
        print(f"| {dimension} | " + " | ".join(ratio(correct, total) for correct, _, total in ratings) + " |")

    print()
    print("## Accuracy by app")
    print()
    print(f"| App | {pass_columns} |")
    print(f"| --- |{right_columns}")
    for app in labels["apps"]:
        subset = [row for row in rows if row["app"] == app["name"]]
        ratings = [metrics(counts(index, subset)) for index in range(len(passes))]
        print(f"| {app['name']} | " + " | ".join(ratio(correct, total) for correct, _, total in ratings) + " |")

    print()
    print("## Mismatches and abstentions")
    print()
    print("This table includes every field where at least one pass missed or withheld the answer.")
    print()
    print(f"| App and field | Expected | {pass_columns} |")
    print("| --- | --- |" + " --- |" * len(passes))
    for row in rows:
        if all(grade == "correct" for grade in row["grades"]):
            continue
        field = FIELD_NAMES[row["field"]]
        outcomes = " | ".join(f"{claim} ({status})" for claim, status in zip(row["claims"], row["grades"], strict=True))
        print(
            f"| {row['app']} · {field} | {row['expected']} [Source]({row['source']}) | "
            f"{outcomes} |"
        )

    print()
    print("## Unscored fields")
    print()
    for app, field, reason in unknown:
        print(f"- {app} · **{field}.** {reason}")
    print()
    print(
        "This small, stratified sample measures agreement with the published documentation. "
        "The test covered documented access paths."
    )
    print()
    print(f"Frozen labels SHA-256 `{hashlib.sha256(raw_labels).hexdigest()}`")


if __name__ == "__main__":
    main()
