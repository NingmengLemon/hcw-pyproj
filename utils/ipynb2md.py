import os
import re

import mdformat
import nbformat
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import Preprocessor


def return_available(filename, *possi_paths: str):
    for path in possi_paths:
        if os.path.isfile(file := os.path.join(path, filename)):
            return file


PLACE_HOLDER_BEGIN = "{{place_holder_toolong_output_begin}}"
PLACE_HOLDER_END = "{{place_holder_toolong_output_end}}"
REGEX_PAIR = re.compile(
    re.escape(PLACE_HOLDER_BEGIN) + "(.*?)" + re.escape(PLACE_HOLDER_END), re.DOTALL
)
REGEX_INDENT_FORW = re.compile(r"^\s{4}", re.MULTILINE)


class CellOutputWrappingPreprocessor(Preprocessor):
    def preprocess_cell(self, cell: dict, resources: dict, index: int):
        if cell["cell_type"] == "code":
            if "outputs" in cell:
                for output in cell["outputs"]:
                    if (text := output.get("text", "")):
                        output["text"] = (
                            f"{PLACE_HOLDER_BEGIN}\n" + text + f"\n{PLACE_HOLDER_END}"
                        )
        return cell, resources


def indent_forward(text):
    return REGEX_INDENT_FORW.sub("", text)


def postprocess_wrapped(mdtext: str):
    return mdformat.text(
        REGEX_PAIR.sub(
            lambda x: "\n<details><summary>Output</summary>\n\n```txt\n"
            + indent_forward(x.group(1)).strip()
            + "\n```\n\n</details>",
            mdtext,
        ),
        options={
            "end-of-line": "keep",
        }
    )


exporter = MarkdownExporter()
exporter.register_preprocessor(CellOutputWrappingPreprocessor(), True)


def convert_one(filepath: str):
    file_noext, ext = os.path.splitext(filepath)
    if ext.lower() == ".ipynb":
        with open(filepath, "r", encoding="utf-8") as fp:
            nb = nbformat.read(fp, as_version=4)
        md, _ = exporter.from_notebook_node(nb)
        # print(_)
        with open(file_noext + ".md", "w+", encoding="utf-8") as fp:
            fp.write(postprocess_wrapped(md))
        print("converted:", filepath)


def main():
    folder = "./docs"
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            file = os.path.join(root, filename)
            convert_one(file)


if __name__ == "__main__":
    main()
