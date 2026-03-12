from fastapi import APIRouter, HTTPException
from models.dataset import GenerateDatasetRequest, GenerateDatasetResponse, QAPair
from services.dataset_generator import generate_dataset

router = APIRouter(prefix="/generate-dataset", tags=["dataset"])


@router.post("", response_model=GenerateDatasetResponse)
async def generate(req: GenerateDatasetRequest) -> GenerateDatasetResponse:
    if not req.documents:
        raise HTTPException(status_code=400, detail="At least one document is required")

    raw_pairs = await generate_dataset(req.documents, req.num_questions)

    pairs = []
    for p in raw_pairs:
        pairs.append(QAPair(
            question=p.get("question", ""),
            answer=p.get("answer", ""),
            ground_truth=p.get("ground_truth", p.get("answer", "")),
            contexts=p.get("contexts", []),
            evolution_type=p.get("evolution_type", "simple"),
        ))

    return GenerateDatasetResponse(
        pairs=pairs,
        total=len(pairs),
        source_documents=len(req.documents),
    )
