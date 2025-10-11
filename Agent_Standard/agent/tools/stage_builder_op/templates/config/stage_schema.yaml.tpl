type: object
required: ['io']
properties:
  io:
    type: object
    required: ['out_doc_path', 'out_stats_path']
    properties:
      out_doc_path:
        type: string
      out_stats_path:
        type: string
