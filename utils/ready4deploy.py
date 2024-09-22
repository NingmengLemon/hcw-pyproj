import os
import re
import shutil
from typing import Optional

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
REGEX_LINK_IPYNB = re.compile(r"\[(.*?)\]\((.*?\.ipynb)(#[^)]*)?\)")


class CellOutputWrappingPreprocessor(Preprocessor):
    def preprocess_cell(self, cell: dict, resources: dict, index: int):
        if cell["cell_type"] == "code":
            if "outputs" in cell:
                for output in cell["outputs"]:
                    if text := output.get("text", ""):
                        output["text"] = (
                            f"{PLACE_HOLDER_BEGIN}\n" + text + f"\n{PLACE_HOLDER_END}"
                        )
        return cell, resources


def indent_forward(text: str):
    return REGEX_INDENT_FORW.sub("", text)


def format_md(md):
    return mdformat.text(
        md,
        options={
            "end-of-line": "keep",
        },
    )


def postprocess_wrapped(mdtext: str):
    return format_md(
        REGEX_PAIR.sub(
            lambda x: "\n<details><summary>Output</summary>\n\n```txt\n"
            + indent_forward(x.group(1)).strip()
            + "\n```\n\n</details>",
            mdtext,
        )
    )


exporter = MarkdownExporter()
exporter.register_preprocessor(CellOutputWrappingPreprocessor(), True)


def update_ipynb_ref(md):
    def replace_link(match: re.Match):
        text = match.group(1)
        ipynb_link = match.group(2)
        anchor = match.group(3) if match.group(3) else ""

        md_link = ipynb_link.replace(".ipynb", ".md")
        return f"[{text}]({md_link}{anchor})"

    return REGEX_LINK_IPYNB.sub(replace_link, md)


def convert_one(filepath: str, saveas: Optional[str] = None):
    file_noext, ext = os.path.splitext(filepath)
    ext = ext.lower()
    match ext:
        case ".ipynb":
            with open(filepath, "r", encoding="utf-8") as fp:
                nb = nbformat.read(fp, as_version=4)
            md, _ = exporter.from_notebook_node(nb)
            tofile = file_noext + ".md" if saveas is None else saveas
            with open(tofile, "w+", encoding="utf-8") as fp:
                fp.write(postprocess_wrapped(md))
            print("converted:", filepath)
        case ".md":
            with open(filepath, "r", encoding="utf-8") as fp:
                md = fp.read()
            tofile = file_noext + ".conv.md" if saveas is None else saveas
            with open(tofile, "w+", encoding="utf-8") as fp:
                fp.write(format_md(update_ipynb_ref(md)))
            print("converted:", filepath)


def main():
    fromfolder = os.path.normpath("./docs")
    tofolder = os.path.normpath("./deploy")
    slash = os.path.normpath("/")
    if os.path.isdir(tofolder):
        shutil.rmtree(tofolder)
        print("deleted:", tofolder)
    for root, _, filenames in os.walk(fromfolder):
        toroot = root.replace(fromfolder, tofolder)
        if root.endswith(slash + "static"):
            shutil.copytree(root, toroot, dirs_exist_ok=True)
            print("copied:", root)
            continue
        if root.endswith(slash + "samples"):
            print("skipped:", root)
            continue
        
        for filename in filenames:
            os.makedirs(toroot, exist_ok=True)

            fromfile = os.path.join(root, filename)
            tofile = os.path.join(toroot, filename)
            convert_one(fromfile, tofile)


if __name__ == "__main__":
    main()
