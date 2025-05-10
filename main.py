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
def extract_text(pdf_url):
    response = requests.get(pdf_url, stream=True)
    response.raise_for_status()

    buf = BytesIO(response.content)
    source = DocumentStream(name="sample.pdf", stream=buf)

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

    result = converter.convert(source)

    markdown = result.document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
    return markdown


@app.local_entrypoint()
def main():
    print(extract_text.remote("https://css4.pub/2017/newsletter/drylab.pdf"))