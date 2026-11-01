import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Convert docx to pdf")
    parser.add_argument("--input", "-i", required=True, help="Input .docx file path")
    parser.add_argument("--output", "-o", help="Output .pdf file path")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_path.lower().endswith(".docx"):
        raise ValueError("Input file must be a .docx file")

    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = os.path.splitext(input_path)[0] + ".pdf"

    try:
        from docx2pdf import convert
    except ImportError as exc:
        raise RuntimeError(
            "docx2pdf is not installed. Run: pip install docx2pdf"
        ) from exc

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    convert(input_path, output_path)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    main()
