"""REST endpoints for prompt template CRUD (disk file operations)."""

from fastapi import APIRouter, HTTPException

from backend.schemas.template import (
    BuildPreviewRequest,
    BuildPreviewResponse,
    TemplateCreate,
    TemplateMetadata,
    TemplateResponse,
    TemplateUpdate,
)
from backend.services import prompt_builder

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("", response_model=list[TemplateMetadata])
def list_templates():
    """List all template files in ``data/templates/``."""
    try:
        return prompt_builder.list_template_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_name}", response_model=TemplateResponse)
def get_template(file_name: str):
    """Read a single template file by name."""
    tmpl = prompt_builder.read_template_file(file_name)
    if tmpl is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {file_name}")
    body_text = tmpl["body"]
    return TemplateResponse(
        file_name=tmpl["file_name"],
        frontmatter=tmpl["frontmatter"],
        body=body_text,
        token_estimate=prompt_builder.estimate_tokens(body_text),
    )


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(body: TemplateCreate):
    """Create a new template file."""
    try:
        result = prompt_builder.write_template_file(
            body.file_name, body.frontmatter, body.body
        )
        body_text = result["body"]
        return TemplateResponse(
            file_name=result["file_name"],
            frontmatter=result["frontmatter"],
            body=body_text,
            token_estimate=prompt_builder.estimate_tokens(body_text),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{file_name}", response_model=TemplateResponse)
def update_template(file_name: str, body: TemplateUpdate):
    """Update an existing template's frontmatter and/or body."""
    existing = prompt_builder.read_template_file(file_name)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {file_name}")

    new_frontmatter = body.frontmatter if body.frontmatter is not None else existing["frontmatter"]
    new_body = body.body if body.body is not None else existing["body"]

    try:
        result = prompt_builder.write_template_file(file_name, new_frontmatter, new_body)
        body_text = result["body"]
        return TemplateResponse(
            file_name=result["file_name"],
            frontmatter=result["frontmatter"],
            body=body_text,
            token_estimate=prompt_builder.estimate_tokens(body_text),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{file_name}", status_code=204)
def delete_template(file_name: str):
    """Delete a template file. Default templates cannot be deleted."""
    try:
        deleted = prompt_builder.delete_template_file(file_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Template not found: {file_name}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/build-preview", response_model=BuildPreviewResponse)
def build_preview(body: BuildPreviewRequest):
    """Preview prompt rendering with given variable values."""
    tmpl = prompt_builder.read_template_file(body.file_name)
    if tmpl is None:
        raise HTTPException(status_code=404, detail=f"Template not found: {body.file_name}")

    try:
        prompt = prompt_builder.build_prompt(tmpl, body.variables)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return BuildPreviewResponse(
        prompt=prompt,
        token_estimate=prompt_builder.estimate_tokens(prompt),
    )
