# Validation Schemas

### DetectType Stage Stats Artifact
- id: `https://medflux.example/schemas/validation/artifacts/detect_type/stage_stats.schema.json`
- file: `core/validation/contracts/artifacts/detect_type/stage_stats.schema.json`
- required: stage, total_items, versioning
- properties:
  - `stage`: const=detect_type (const=detect_type)
  - `total_items`: integer
  - `counts`: object
  - `versioning`: object

### DetectType Unified Document Artifact
- id: `https://medflux.example/schemas/validation/artifacts/detect_type/unified_document.schema.json`
- file: `core/validation/contracts/artifacts/detect_type/unified_document.schema.json`
- required: stage, items, versioning
- properties:
  - `stage`: const=detect_type (const=detect_type)
  - `items`: array
  - `versioning`: object

### Encoding Stage Stats Artifact
- id: `https://medflux.example/schemas/validation/artifacts/encoding/stage_stats.schema.json`
- file: `core/validation/contracts/artifacts/encoding/stage_stats.schema.json`
- required: stage, total_items, versioning
- properties:
  - `stage`: const=encoding (const=encoding)
  - `total_items`: integer
  - `normalized`: integer/null
  - `failed_normalizations`: integer/null
  - `with_bom`: integer/null
  - `utf8_native`: integer/null
  - `versioning`: object

### Encoding Unified Document Artifact
- id: `https://medflux.example/schemas/validation/artifacts/encoding/unified_document.schema.json`
- file: `core/validation/contracts/artifacts/encoding/unified_document.schema.json`
- required: stage, items, versioning
- properties:
  - `stage`: const=encoding (const=encoding)
  - `items`: array
  - `versioning`: object

### Readers Doc Meta Artifact
- id: `https://medflux.example/schemas/validation/artifacts/readers/doc_meta.schema.json`
- file: `core/validation/contracts/artifacts/readers/doc_meta.schema.json`
- required: documents, versioning
- properties:
  - `documents`: array
  - `versioning`: object

### Readers Stage Stats Artifact
- id: `https://medflux.example/schemas/validation/artifacts/readers/stage_stats.schema.json`
- file: `core/validation/contracts/artifacts/readers/stage_stats.schema.json`
- required: documents, items_processed, versioning
- properties:
  - `documents`: integer
  - `items_processed`: integer
  - `avg_conf`: number/null
  - `warnings`: integer/null
  - `versioning`: object

### Readers Summary Artifact
- id: `https://medflux.example/schemas/validation/artifacts/readers/summary.schema.json`
- file: `core/validation/contracts/artifacts/readers/summary.schema.json`
- required: run_id, pipeline_id, items, stage_stats, versioning
- properties:
  - `run_id`: string
  - `pipeline_id`: string
  - `items`: array
  - `stage_stats`: object
  - `versioning`: object

### Base Artifact Contract
- id: `https://medflux.example/schemas/validation/base/base_contract.schema.json`
- file: `core/validation/contracts/base/base_contract.schema.json`
- required: versioning
- properties:
  - `versioning`: object
- defs:
  - `$defs.versioning`: object

### Document Meta
- file: `core/validation/contracts/base/document_meta.schema.json`
- properties:
  - `pages`: integer
  - `lang_overall`: string/null
  - `has_ocr`: boolean/null

### DetectType - Input
- id: `https://medflux.example/schemas/validation/stages/phase_00_detect_type/input.schema.json`
- file: `core/validation/contracts/stages/phase_00_detect_type/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
- defs:
  - `$defs.input_item`: object

### DetectType - Output
- id: `https://medflux.example/schemas/validation/stages/phase_00_detect_type/output.schema.json`
- file: `core/validation/contracts/stages/phase_00_detect_type/output.schema.json`
- required: run_id, unified_document, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref
- defs:
  - `$defs.detect_item`: object

### Encoding - Input
- id: `https://medflux.example/schemas/validation/stages/phase_01_encoding/input.schema.json`
- file: `core/validation/contracts/stages/phase_01_encoding/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Encoding - Output
- id: `https://medflux.example/schemas/validation/stages/phase_01_encoding/output.schema.json`
- file: `core/validation/contracts/stages/phase_01_encoding/output.schema.json`
- required: run_id, unified_document, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref
- defs:
  - `$defs.encoding_item`: object

### Readers - Input
- id: `https://medflux.example/schemas/validation/stages/phase_02_readers/input.schema.json`
- file: `core/validation/contracts/stages/phase_02_readers/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Readers - Output
- id: `https://medflux.example/schemas/validation/stages/phase_02_readers/output.schema.json`
- file: `core/validation/contracts/stages/phase_02_readers/output.schema.json`
- required: run_id, items, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `stage_stats`: object
  - `versioning`: ref

### Merge - Input
- id: `https://medflux.example/schemas/validation/stages/phase_03_merge/input.schema.json`
- file: `core/validation/contracts/stages/phase_03_merge/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Merge - Output
- id: `https://medflux.example/schemas/validation/stages/phase_03_merge/output.schema.json`
- file: `core/validation/contracts/stages/phase_03_merge/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Cleaning - Input
- id: `https://medflux.example/schemas/validation/stages/phase_04_cleaning/input.schema.json`
- file: `core/validation/contracts/stages/phase_04_cleaning/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Cleaning - Output
- id: `https://medflux.example/schemas/validation/stages/phase_04_cleaning/output.schema.json`
- file: `core/validation/contracts/stages/phase_04_cleaning/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Light Normalization - Input
- id: `https://medflux.example/schemas/validation/stages/phase_05_light_normalization/input.schema.json`
- file: `core/validation/contracts/stages/phase_05_light_normalization/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Light Normalization - Output
- id: `https://medflux.example/schemas/validation/stages/phase_05_light_normalization/output.schema.json`
- file: `core/validation/contracts/stages/phase_05_light_normalization/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Segmentation - Input
- id: `https://medflux.example/schemas/validation/stages/phase_06_segmentation/input.schema.json`
- file: `core/validation/contracts/stages/phase_06_segmentation/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Segmentation - Output
- id: `https://medflux.example/schemas/validation/stages/phase_06_segmentation/output.schema.json`
- file: `core/validation/contracts/stages/phase_06_segmentation/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Table Extraction - Input
- id: `https://medflux.example/schemas/validation/stages/phase_07_table_extraction/input.schema.json`
- file: `core/validation/contracts/stages/phase_07_table_extraction/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Table Extraction - Output
- id: `https://medflux.example/schemas/validation/stages/phase_07_table_extraction/output.schema.json`
- file: `core/validation/contracts/stages/phase_07_table_extraction/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Heavy Normalization - Input
- id: `https://medflux.example/schemas/validation/stages/phase_08_heavy_normalization/input.schema.json`
- file: `core/validation/contracts/stages/phase_08_heavy_normalization/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Heavy Normalization - Output
- id: `https://medflux.example/schemas/validation/stages/phase_08_heavy_normalization/output.schema.json`
- file: `core/validation/contracts/stages/phase_08_heavy_normalization/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Provenance - Input
- id: `https://medflux.example/schemas/validation/stages/phase_09_provenance/input.schema.json`
- file: `core/validation/contracts/stages/phase_09_provenance/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Provenance - Output
- id: `https://medflux.example/schemas/validation/stages/phase_09_provenance/output.schema.json`
- file: `core/validation/contracts/stages/phase_09_provenance/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Offsets - Input
- id: `https://medflux.example/schemas/validation/stages/phase_10_offsets/input.schema.json`
- file: `core/validation/contracts/stages/phase_10_offsets/input.schema.json`
- required: run_id, items
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array

### Offsets - Output
- id: `https://medflux.example/schemas/validation/stages/phase_10_offsets/output.schema.json`
- file: `core/validation/contracts/stages/phase_10_offsets/output.schema.json`
- required: run_id, stage_stats, versioning
- properties:
  - `run_id`: string (format=run-id)
  - `items`: array
  - `unified_document`: object
  - `stage_stats`: object
  - `versioning`: ref

### Page Stat
- file: `core/validation/contracts/types/page_stat.schema.json`
- required: page
- properties:
  - `page`: integer
  - `tables_found`: integer/null
  - `low_conf`: boolean/null

### Table
- file: `core/validation/contracts/types/table.schema.json`
- required: page
- properties:
  - `page`: integer
  - `cells`: integer

### Text Block
- file: `core/validation/contracts/types/text_block.schema.json`
- required: page, text
- properties:
  - `page`: integer
  - `text`: string
  - `bbox`: array
