import modal

from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
from docling_core.types.doc.base import ImageRefMode
import requests
from io import BytesIO

app = modal.App("docling-test")

image = modal.Image.from_registry("lukee/docling")

@app.function(image=image, gpu="A100-40GB")
def docling_extract(buf):
    pipeline_options = PdfPipelineOptions()
    pipeline_options.artifacts_path = "/root/.cache/docling/models"
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.CUDA
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    source = DocumentStream(name="sample.pdf", stream=buf)
    result = converter.convert(source)

    markdown = result.document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
    return markdown

@app.function(image=image)
def extract_text(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    buf = BytesIO(response.content)
    return docling_extract.remote(buf)


@app.local_entrypoint()
def main():
    print(extract_text.remote("https://css4.pub/2017/newsletter/drylab.pdf"))