import os

import nbformat
from traitlets.config import Config
from nbconvert import MarkdownExporter


def return_available(filename, *possi_paths: str):
    for path in possi_paths:
        if os.path.isfile(file := os.path.join(path, filename)):
            return file


config = Config()
# if f := return_available("detailswrapped.md.j2", "./", "./utils/"):
#     config.MarkdownExporter.template_file = f
exporter = MarkdownExporter(config=config)


def convert_one(filepath: str):
    file_noext, ext = os.path.splitext(filepath)
    if ext.lower() == ".ipynb":
        with open(filepath, "r", encoding="utf-8") as fp:
            nb = nbformat.read(fp, as_version=4)
        md, _ = exporter.from_notebook_node(nb)
        with open(file_noext + ".md", "w+", encoding="utf-8") as fp:
            # fp.write(handle_md(md))
            fp.write(md)
        print("converted:", filepath)


# 吗的我要骂人了
def handle_md(md: str):
    result: list[str] = []
    alert = enter = False
    wrapped: list[str] = []
    codeblock_quote_count = 0
    for line in md.splitlines():
        if line == "":
            alert = True
            result.append(line)
            continue
        if line.startswith("```"):
            codeblock_quote_count += 1
        if (
            (alert or enter)
            and line.startswith(" " * 4)
            and codeblock_quote_count % 2 == 0
        ):
            enter = True
            wrapped.append(line.removeprefix(" " * 4))
            continue
        else:
            alert = enter = False
        if wrapped:
            if len(wrapped) > 20:
                wrapped = (
                    [
                        f"<details><summary>Output {len(wrapped)} lines</summary>\n",
                        "```txt",
                    ]
                    + ["\n".join(wrapped).strip()]
                    + [
                        "```",
                        "\n</details>",
                    ]
                )
            result.extend(wrapped)
            wrapped.clear()
        result.append(line)
    return "\n".join(result)


def main():
    folder = "./docs"
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            file = os.path.join(root, filename)
            convert_one(file)


if __name__ == "__main__":
    main()
