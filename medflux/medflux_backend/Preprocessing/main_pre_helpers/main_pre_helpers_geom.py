from typing import List


def validate_bbox(b: List[float]) -> bool:
    return isinstance(b, list) and len(b)==4 and b[2]>b[0] and b[3]>b[1]


def to_bottom_left(bbox, page_h, origin="top-left"):
    if origin=="bottom-left": return bbox
    x1,y1,x2,y2 = bbox
    return [x1, page_h - y2, x2, page_h - y1]
