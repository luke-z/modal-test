FROM python:3.13-slim

RUN pip install docling
RUN docling-tools models download