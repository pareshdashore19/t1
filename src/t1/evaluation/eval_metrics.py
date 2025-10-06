import ast
from typing import List, Dict, Any

from collections import Counter


def extract_tool_calls(code: str) -> List[Dict[str, Any]]:
    tool_calls = []
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if not func_name:
                continue

            args = {}

            for kw in node.keywords:
                try:
                    args[kw.arg] = ast.literal_eval(kw.value)
                except Exception:
                    args[kw.arg] = ast.unparse(kw.value)

            if node.args:
                args["no_key"] = []
                for i, arg in enumerate(node.args):
                    try:
                        args["no_key"].append(ast.literal_eval(arg))
                    except Exception:
                        args["no_key"].append(ast.unparse(arg))
            tool_calls.append({func_name: args})

    return tool_calls


def count_tool_usage(extracted_code: List[Dict[str, Any]]) -> Dict[str, int]:
    key_counter = Counter()
    for d in extracted_code:
        key_counter.update(d.keys())
    key_counter = dict(key_counter)
    return key_counter


# def compare_tool_count_with_gold(actuals, predictions):

#     actuals_tool_count = count_tool_usage(actuals)
#     predictions_tool_count = count_tool_usage(predictions)
#     compare = {}
#     for tool in actuals_tool_count:
#         actuals_count = actuals_tool_count[tool]
#         predcitions_count = predictions_tool_count.get(tool)

#         if actuals_count == predcitions_count:
#             compare[tool] = True

#         else:
#             compare[tool] = False

#     return compare


def calculate_tool_calling_metrics(actuals, predictions):

    actual_tool_count = count_tool_usage(actuals)
    prediction_tool_count = count_tool_usage(predictions)

    all_tools = set(actual_tool_count.keys() | set(prediction_tool_count.keys()))
    tp = 0
    fp = 0
    fn = 0
    total_actuals = 0
    total_predictions = 0

    for tool in all_tools:
        actual_count = actual_tool_count.get(tool, 0)
        prediction_count = prediction_tool_count.get(tool, 0)

        tp += min(actual_count, prediction_count)
        fp += max(0, prediction_count - actual_count)
        fn += max(0, actual_count - prediction_count)

        total_actuals += actual_count
        total_predictions += prediction_count

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    accuracy = tp / (tp + fn + fp) if (tp + fn + fp) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "total_actuals": total_actuals,
        "total_predictions": total_predictions,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
    }


IGNORED_KEYS = {
    "key",
    "value",
    "hotels",
    "restaurants",
    "attractions",
    "prior_results",
    "results",
    "no_key",
}

SKIP_TOOLS = {"seek_information", "save_to_cache", "get_results_from_cache"}


def normalize_value(value):
    if isinstance(value, list):
        try:
            return sorted(value)
        except TypeError:
            return value
    elif isinstance(value, dict):
        return {
            k: normalize_value(v) for k, v in value.items() if k not in IGNORED_KEYS
        }
    else:
        return value


def normalize_dict(d):
    return {k: normalize_value(v) for k, v in d.items() if k not in IGNORED_KEYS}


def calculate_tool_param_metrics(actuals, predictions):

    tp = 0
    total_actual_params = 0
    total_predicted_params = 0
    used_pred_indices = set()

    for actual_call in actuals:
        if not isinstance(actual_call, dict) or len(actual_call) != 1:
            continue
        tool, actual_params = list(actual_call.items())[0]
        if tool in SKIP_TOOLS:
            continue

        actual_params = normalize_dict(actual_params)
        total_actual_params += len(actual_params)

        # Filter predictions by tool name and unused
        candidates = []
        for i, pred in enumerate(predictions):
            if not isinstance(pred, dict) or len(pred) != 1:
                continue
            pred_tool, pred_params = list(pred.items())[0]
            if (
                pred_tool == tool
                and i not in used_pred_indices
                and pred_tool not in SKIP_TOOLS
            ):
                candidates.append((i, normalize_dict(pred_params)))

        if not candidates:
            continue

        best_match_idx = -1
        best_match_count = -1
        best_match_params = {}

        for i, cand_params in candidates:
            match_count = sum(
                actual_params.get(k) == cand_params.get(k)
                for k in actual_params
                if k in cand_params
            )

            if match_count > best_match_count:
                best_match_count = match_count
                best_match_idx = i
                best_match_params = cand_params

        if best_match_idx != -1:
            used_pred_indices.add(best_match_idx)
            tp += best_match_count
            total_predicted_params += len(best_match_params)

    # Handle unmatched predictions
    for i, pred_call in enumerate(predictions):
        if (
            i in used_pred_indices
            or not isinstance(pred_call, dict)
            or len(pred_call) != 1
        ):
            continue
        tool, params = list(pred_call.items())[0]
        if tool in SKIP_TOOLS:
            continue
        total_predicted_params += len([k for k in params if k not in IGNORED_KEYS])

    fp = total_predicted_params - tp
    fn = total_actual_params - tp
    precision = tp / total_predicted_params if total_predicted_params else 0
    recall = tp / total_actual_params if total_actual_params else 0
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "total_actual_params": total_actual_params,
        "total_predicted_params": total_predicted_params,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
    }


# IGNORED_KEYS = {
#     "get_results_from_cache": "key",
#     "save_to_cache": ["key", "value"],
#     "search_nearest": ["hotels", "restaurants", "attractions"],
#     "filter_flights": "prior_results",
#     "filter_hotels": "prior_results",
#     "filter_attractions": "prior_results",
#     "filter_restaurants": "prior_results",
#     "sort_results": "results",
#     "seek_information": "no_key",
# }

# SKIP_KEYS = {"seek_information", "save_to_cache", "get_results_from_cache"}


# def normalize_value(value):
#     if isinstance(value, list):
#         return sorted(value)
#     elif isinstance(value, dict):
#         return {k: normalize_value(v) for k, v in value.items()}
#     return value


# def normalize_dict(d):
#     if not isinstance(d, dict) or len(d) != 1:
#         return d
#     top_key = next(iter(d))
#     sub_dict = d[top_key]
#     if top_key in IGNORED_KEYS and isinstance(sub_dict, dict):
#         sub_dict = {k: v for k, v in sub_dict.items() if k not in IGNORED_KEYS[top_key]}
#     return {top_key: normalize_value(sub_dict)}


# def is_skipped(item):
#     if isinstance(item, dict) and len(item) == 1:
#         return next(iter(item)) in SKIP_KEYS
#     return False


# def make_hashable(obj):
#     if isinstance(obj, dict):
#         return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
#     elif isinstance(obj, list):
#         return tuple(sorted(make_hashable(i) for i in obj))
#     else:
#         return obj


# def calculate_tool_param_metrics(extracted_gold, extracted_gen):
#     norm_gold = [
#         make_hashable(normalize_dict(i)) for i in extracted_gold if not is_skipped(i)
#     ]
#     norm_gen = [
#         make_hashable(normalize_dict(i)) for i in extracted_gen if not is_skipped(i)
#     ]

#     used_indices = set()
#     tp = 0
#     for actual_item in norm_gold:
#         for i, predicted_item in enumerate(norm_gen):
#             if i in used_indices:
#                 continue
#             if actual_item == predicted_item:
#                 tp += 1
#                 used_indices.add(i)
#                 break

#     fp = len(norm_gen) - tp
#     fn = len(norm_gold) - tp

#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
#     recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
#     f1 = (
#         (2 * precision * recall) / (precision + recall)
#         if (precision + recall) > 0
#         else 0.0
#     )

#     total = len(norm_gold) + fp
#     accuracy = tp / total if total > 0 else 0.0

#     return {
#         "tp": tp,
#         "fp": fp,
#         "fn": fn,
#         "precision": round(precision, 4),
#         "recall": round(recall, 4),
#         "f1": round(f1, 4),
#         "accuracy": round(accuracy, 4),
#     }


# def get_tool_param_match(main, comparison):
#     norm_comparison = [normalize_dict(item) for item in comparison]
#     flags = []
#     for item in main:
#         if isinstance(item, dict) and len(item) == 1:
#             top_key = next(iter(item))
#             if top_key in SKIP_KEYS:
#                 flags.append("skip")
#                 continue
#         norm_item = normalize_dict(item)
#         flags.append(norm_item in norm_comparison)
#     return flags
