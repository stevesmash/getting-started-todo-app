"""Bulk import and export endpoints."""

import csv
import json
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import Response

from app.dependencies import get_current_user
from app.schemas import Entity, EntityCreate
from app.storage import store

router = APIRouter(prefix="/import", tags=["import"])
export_router = APIRouter(prefix="/export", tags=["export"])


@router.post("/entities", response_model=dict)
async def bulk_import_entities(
    case_id: int = Form(...),
    file: UploadFile = File(...),
    user: str = Depends(get_current_user)
):
    """Import entities from CSV or JSON file."""
    
    try:
        store.get_case(owner=user, case_id=case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    
    content = await file.read()
    content_str = content.decode('utf-8')
    
    entities_data = []
    
    if file.filename.endswith('.json'):
        try:
            data = json.loads(content_str)
            if isinstance(data, list):
                entities_data = data
            else:
                raise HTTPException(status_code=400, detail="JSON must be an array of entities")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    elif file.filename.endswith('.csv'):
        try:
            reader = csv.DictReader(io.StringIO(content_str))
            entities_data = list(reader)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV: {str(e)}")
    
    else:
        raise HTTPException(status_code=400, detail="File must be .csv or .json")
    
    created = []
    errors = []
    
    for i, item in enumerate(entities_data):
        try:
            name = item.get('name', '').strip()
            kind = item.get('kind', item.get('type', '')).strip()
            description = item.get('description', '').strip()
            
            if not name:
                errors.append(f"Row {i+1}: Missing name")
                continue
            if not kind:
                errors.append(f"Row {i+1}: Missing kind/type")
                continue
            
            payload = EntityCreate(
                case_id=case_id,
                name=name,
                kind=kind,
                description=description or None
            )
            entity = store.create_entity(owner=user, payload=payload)
            created.append(entity)
            
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    if created:
        store.log_activity(
            owner=user,
            action="created",
            resource_type="entity",
            resource_name=f"Bulk import ({len(created)} entities)",
            details=f"Imported from {file.filename}"
        )
    
    return {
        "imported": len(created),
        "errors": errors,
        "message": f"Successfully imported {len(created)} entities" + (f" with {len(errors)} errors" if errors else "")
    }


@export_router.get("/case/{case_id}")
async def export_case(
    case_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    user: str = Depends(get_current_user)
):
    """Export a case with all its entities and relationships."""
    
    try:
        case = store.get_case(owner=user, case_id=case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Case not found")
    
    entities = [e for e in store.list_entities(owner=user) if e.case_id == case_id]
    relationships = store.list_relationships(owner=user)
    entity_ids = {e.id for e in entities}
    case_relationships = [
        r for r in relationships 
        if r.source_id in entity_ids or r.target_id in entity_ids
    ]
    
    export_data = {
        "case": {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "created_at": case.created_at.isoformat() if case.created_at else None
        },
        "entities": [
            {
                "id": e.id,
                "name": e.name,
                "kind": e.kind,
                "description": e.description
            }
            for e in entities
        ],
        "relationships": [
            {
                "id": r.id,
                "source_id": r.source_id,
                "target_id": r.target_id,
                "relation": r.relation
            }
            for r in case_relationships
        ]
    }
    
    if format == "json":
        content = json.dumps(export_data, indent=2)
        media_type = "application/json"
        filename = f"case_{case_id}_export.json"
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "id", "name", "kind", "description", "source_id", "target_id", "relation"])
        writer.writerow(["case", case.id, case.name, "", case.description or "", "", "", ""])
        for e in entities:
            writer.writerow(["entity", e.id, e.name, e.kind, e.description or "", "", "", ""])
        for r in case_relationships:
            writer.writerow(["relationship", r.id, "", "", "", r.source_id, r.target_id, r.relation])
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"case_{case_id}_export.csv"
    
    store.log_activity(
        owner=user,
        action="exported",
        resource_type="case",
        resource_name=case.name,
        details=f"Exported as {format}"
    )
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
