import argparse
import json
import sys

from .logger import get_separation_logger
from .model_download import download_all, download_model
from .model_registry import create_separator, list_models, resolve_model


def _parse_key_value(values):
    result = {}
    for value in values or []:
        if "=" not in value:
            raise argparse.ArgumentTypeError(f"Expected key=value, got {value!r}")
        key, raw = value.split("=", 1)
        lowered = raw.lower()
        if lowered in {"true", "false"}:
            result[key] = lowered == "true"
        else:
            try:
                result[key] = int(raw)
            except ValueError:
                try:
                    result[key] = float(raw)
                except ValueError:
                    result[key] = raw
    return result


def _add_common_runtime_args(parser):
    parser.add_argument("-i", "--input", required=True, help="Input audio folder.")
    parser.add_argument("-o", "--output", default="results", help="Output folder.")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    parser.add_argument("--device-id", action="append", type=int, dest="device_ids", help="CUDA device id. Can be repeated.")
    parser.add_argument("--format", default="wav", choices=["wav", "flac", "mp3", "m4a"], dest="output_format")
    parser.add_argument("--tta", action="store_true", help="Enable test time augmentation.")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--param", action="append", default=[], help="Inference override as key=value, for example --param batch_size=2.")


def cmd_list(args):
    rows = list_models(category=args.category, supported=None if args.all else True)
    if args.json:
        print(json.dumps([item.__dict__ for item in rows], ensure_ascii=False, indent=2))
        return 0
    for item in rows:
        status = "ok" if item.supported else item.unsupported_reason
        category = item.category_path or item.primary_category
        print(f"{item.name}\t{item.model_type or item.architecture}\t{category}\t{item.target_stem}\t{status}")
    return 0


def cmd_info(args):
    resolved = resolve_model(args.model, model_dir=args.model_dir, require_supported=False, require_exists=False)
    entry = resolved["entry"]
    data = {
        "name": entry.name,
        "model_type": entry.model_type,
        "architecture": entry.architecture,
        "supported": entry.supported,
        "unsupported_reason": entry.unsupported_reason,
        "category": entry.category_path or entry.primary_category,
        "category_cn": " / ".join(filter(None, [entry.primary_category_cn, entry.secondary_category_cn])),
        "target_stem": entry.target_stem,
        "model_path": resolved["model_path"],
        "config_path": resolved["config_path"],
        "size_bytes": entry.size_bytes,
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_download(args):
    if args.model == "all":
        results = download_all(
            model_dir=args.model_dir,
            source=args.source,
            endpoint=args.endpoint,
            supported_only=args.supported_only,
            force=args.force,
        )
        failed = [item for item in results if item.get("error")]
        print(f"Downloaded/skipped {len(results) - len(failed)} model(s), failed {len(failed)}.")
        for item in failed:
            print(f"ERROR {item['entry'].name}: {item['error']}", file=sys.stderr)
        return 1 if failed else 0

    result = download_model(
        args.model,
        model_dir=args.model_dir,
        source=args.source,
        endpoint=args.endpoint,
        force=args.force,
    )
    _print_download_result(result)
    return 0


def _print_download_result(result):
    for path in result["skipped"]:
        print(f"exists {path}")
    for path in result["downloaded"]:
        print(f"downloaded {path}")


def _ensure_model_files(args):
    try:
        resolve_model(args.model, model_dir=args.model_dir, require_supported=True, require_exists=True)
    except FileNotFoundError:
        result = download_model(args.model, model_dir=args.model_dir, source=args.source, endpoint=args.endpoint)
        _print_download_result(result)
    else:
        if args.download:
            result = download_model(args.model, model_dir=args.model_dir, source=args.source, endpoint=args.endpoint)
            _print_download_result(result)


def cmd_infer(args):
    _ensure_model_files(args)
    logger = get_separation_logger()
    separator = create_separator(
        args.model,
        model_dir=args.model_dir,
        device=args.device,
        device_ids=args.device_ids or [0],
        output_format=args.output_format,
        use_tta=args.tta,
        store_dirs=args.output,
        logger=logger,
        debug=args.debug,
        inference_params=_parse_key_value(args.param),
    )
    files = separator.process_folder(args.input)
    separator.del_cache()
    print(f"Processed {len(files)} file(s).")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="pymss", description="pymss model downloader and inference CLI.")
    parser.add_argument(
        "--model-dir",
        help="Local model cache directory. Defaults to PYMSS_MODEL_DIR, repository all_models if present, or ~/.cache/pymss/models.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List known models.")
    list_parser.add_argument("--category", help="Filter by primary or secondary category.")
    list_parser.add_argument("--all", action="store_true", help="Include models that are not supported for inference yet.")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(func=cmd_list)

    info_parser = subparsers.add_parser("info", help="Show model metadata.")
    info_parser.add_argument("model")
    info_parser.set_defaults(func=cmd_info)

    download_parser = subparsers.add_parser("download", help="Download a model by name, or use 'all'.")
    download_parser.add_argument("model")
    download_parser.add_argument("--source", default="modelscope", choices=["modelscope", "huggingface", "hf-mirror"])
    download_parser.add_argument("--endpoint", help="Custom resolve endpoint. It must serve files by relative path.")
    download_parser.add_argument("--force", action="store_true")
    download_parser.add_argument("--supported-only", action="store_true", help="Only used with model='all'.")
    download_parser.set_defaults(func=cmd_download)

    infer_parser = subparsers.add_parser("infer", help="Run inference by model name.")
    infer_parser.add_argument("model")
    infer_parser.add_argument(
        "--download",
        action="store_true",
        help="Check/download the model before inference. Missing model files are downloaded automatically.",
    )
    infer_parser.add_argument("--source", default="modelscope", choices=["modelscope", "huggingface", "hf-mirror"])
    infer_parser.add_argument("--endpoint", help="Custom resolve endpoint. It must serve files by relative path.")
    _add_common_runtime_args(infer_parser)
    infer_parser.set_defaults(func=cmd_infer)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"pymss: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
