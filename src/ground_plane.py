"""แปลงพิกัดพิกเซลในภาพให้เป็นระยะจริงบนพื้น (หน่วยเซนติเมตร) — โครงของ Phase 2

ไฟล์นี้ยังไม่ถูกเรียกใช้จาก ``detect.py`` เป็นโครงไว้ล่วงหน้าเท่านั้น
ยังต้องมีรูปจุดอ้างอิงจริงก่อนจึงจะใช้งานได้

ทำไมต้องมีไฟล์นี้
-----------------
``detect.py`` บอกได้แค่ว่าวัชพืชอยู่ตรงไหน "ในภาพ" เป็นพิกเซล ซึ่งเอาไปสั่งหุ่นไม่ได้
เพราะพิกเซลไม่ได้บอกว่าไกลกี่เซนติเมตร วัตถุที่อยู่ไกลจะดูเล็กและอยู่สูงในภาพ
ส่วนวัตถุใกล้จะดูใหญ่และอยู่ล่างในภาพ ทั้งที่ขนาดจริงอาจเท่ากัน

homography คือตารางตัวเลข 3x3 ที่บอกความสัมพันธ์ระหว่าง "จุดในภาพ" กับ "จุดบนพื้นราบ"
เมื่อคำนวณได้ครั้งเดียวแล้ว จะใช้แปลงจุดไหนก็ได้ในภาพนั้น ตราบใดที่กล้องยังอยู่ที่มุมและ
ความสูงเดิม

ระบบพิกัดที่ใช้
---------------
พิกัดบนพื้นในไฟล์นี้เป็นพิกัด "เทียบกับตัวหุ่น" ไม่ใช่พิกัดของสวน::

    X = ระยะด้านข้าง หน่วยเซนติเมตร (บวก = ขวาของหุ่น, ลบ = ซ้าย)
    Y = ระยะไปข้างหน้า หน่วยเซนติเมตร (บวก = หน้าหุ่น)
    จุด (0, 0) = จุดบนพื้นที่อยู่ใต้กึ่งกลางตัวหุ่น

เนื่องจากหุ่นตัวนี้ไถลไปบนพื้นได้เอง จุด ``(0, 0)`` จึงเลื่อนตามตัวหุ่นตลอดเวลา
ค่าที่ได้จากไฟล์นี้จึงใช้ได้เฉพาะกับ "ภาพนั้น ณ วินาทีนั้น" เท่านั้น การจะรู้ว่าวัชพืช
ต้นนั้นอยู่ตรงไหนของสวนต้องรอเรื่อง localization ซึ่งยังไม่มีคำตอบ
ดูรายละเอียดใน ``docs/CHAT_HANDOFF_TH.md``

วิธีถ่ายรูปจุดอ้างอิง
--------------------
ทำครั้งเดียวต่อการติดตั้งกล้องหนึ่งแบบ ถ้าขยับกล้องหรือเปลี่ยนมุมต้องทำใหม่

1. ติดกล้องบนตัวหุ่นให้เรียบร้อยก่อน ที่ความสูงและมุมก้มที่จะใช้จริง
   **ห้ามถือกล้องถ่ายเอง** เพราะมุมจะไม่ตรงกับตอนใช้งาน
2. หาพื้นราบ ๆ วางของเล็ก ๆ ที่เห็นชัดเป็นจุดอ้างอิง 4 จุด เช่น เทปกาวสีตัดกับพื้น
   ฝาขวด หรือหมุด วางเป็นสี่เหลี่ยมผืนผ้าจะวัดง่ายที่สุด
3. ใช้ตลับเมตรวัดระยะจริงระหว่างจุดทั้ง 4 แล้วจดไว้เป็นเซนติเมตร วัดจากตัวหุ่นด้วย
   ว่าจุดแต่ละจุดอยู่หน้าหุ่นกี่ ซม. และเยื้องซ้ายขวากี่ ซม.
4. ถ่ายรูป 1 รูปให้เห็นครบทั้ง 4 จุด โดยกล้องอยู่นิ่ง หุ่นไม่ขยับ
5. เปิดรูปในโปรแกรมดูภาพที่บอกพิกัดพิกเซลได้ แล้วจดพิกเซล ``(x, y)`` ของแต่ละจุด
6. เอาตัวเลขทั้งสองชุดมาใส่ใน :meth:`GroundPlane.from_reference_points`

ข้อควรระวัง: จุดอ้างอิงทั้ง 4 ต้องอยู่ **บนพื้นระนาบเดียวกัน** ห้ามวางบนของที่สูงขึ้นมา
และควรวางให้กระจายครอบคลุมบริเวณที่หุ่นจะทำงานจริง ไม่ใช่กระจุกอยู่มุมเดียว

ข้อจำกัดที่ต้องรู้
-----------------
homography ใช้ได้เฉพาะสิ่งที่อยู่ติดพื้นเท่านั้น ส่วนของพืชที่สูงขึ้นมาจากพื้นจะแปลง
ออกมาเพี้ยน (ยิ่งสูงยิ่งเพี้ยน) โค้ดนี้จึงใช้ "ขอบล่างกึ่งกลางของกรอบ" เป็นจุดแทนตำแหน่ง
เพราะเป็นจุดที่ใกล้เคียงจุดที่ต้นไม้สัมผัสพื้นที่สุด และถ้าพื้นเอียงหรือเป็นเนิน
ค่าที่ได้จะคลาดเคลื่อนทั้งภาพ
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


# จำนวนจุดอ้างอิงขั้นต่ำที่ cv2.findHomography ต้องการ
MIN_REFERENCE_POINTS = 4

PointPx = tuple[float, float]
PointCm = tuple[float, float]
BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class GroundPoint:
    """ตำแหน่งบนพื้นเทียบกับตัวหุ่น หน่วยเซนติเมตร"""

    x_cm: float
    y_cm: float

    @property
    def distance_cm(self) -> float:
        """ระยะตรงจากกึ่งกลางหุ่นถึงจุดนั้น"""
        return float(np.hypot(self.x_cm, self.y_cm))

    def to_dict(self) -> dict:
        return {
            "x_cm": round(self.x_cm, 1),
            "y_cm": round(self.y_cm, 1),
            "distance_cm": round(self.distance_cm, 1),
        }


class GroundPlane:
    """เก็บ homography และใช้แปลงพิกเซลเป็นเซนติเมตรบนพื้น"""

    def __init__(self, matrix: np.ndarray) -> None:
        if matrix.shape != (3, 3):
            raise ValueError("homography matrix ต้องมีขนาด 3x3")
        self.matrix = matrix.astype(np.float64)

    @classmethod
    def from_reference_points(
        cls,
        image_points: list[PointPx],
        ground_points: list[PointCm],
    ) -> "GroundPlane":
        """คำนวณ homography จากจุดอ้างอิงที่วัดระยะจริงไว้แล้ว

        Args:
            image_points: พิกัดพิกเซล ``(x, y)`` ของจุดอ้างอิงในรูป อย่างน้อย 4 จุด
            ground_points: พิกัดจริงบนพื้น ``(x_cm, y_cm)`` ของจุดเดียวกัน
                **เรียงลำดับให้ตรงกับ image_points**

        ถ้าใส่เกิน 4 จุดจะแม่นขึ้น เพราะ OpenCV จะเฉลี่ยความคลาดเคลื่อนจากการวัดให้
        """
        if len(image_points) != len(ground_points):
            raise ValueError("จำนวนจุดในภาพกับจุดบนพื้นต้องเท่ากันและเรียงตรงกัน")
        if len(image_points) < MIN_REFERENCE_POINTS:
            raise ValueError(
                f"ต้องมีจุดอ้างอิงอย่างน้อย {MIN_REFERENCE_POINTS} จุด "
                f"แต่ได้มา {len(image_points)} จุด"
            )

        source = np.array(image_points, dtype=np.float64).reshape(-1, 1, 2)
        target = np.array(ground_points, dtype=np.float64).reshape(-1, 1, 2)

        matrix, _mask = cv2.findHomography(source, target, method=0)
        if matrix is None:
            raise ValueError(
                "คำนวณ homography ไม่สำเร็จ มักเกิดจากจุดอ้างอิงเรียงเป็นเส้นตรง "
                "หรืออยู่ใกล้กันเกินไป ลองวางจุดให้กระจายเป็นสี่เหลี่ยมแล้วถ่ายใหม่"
            )
        return cls(matrix)

    def pixel_to_ground(self, point: PointPx) -> GroundPoint:
        """แปลงจุดพิกเซล 1 จุดเป็นตำแหน่งบนพื้น"""
        source = np.array([[point]], dtype=np.float64)
        mapped = cv2.perspectiveTransform(source, self.matrix)
        x_cm, y_cm = mapped[0][0]
        return GroundPoint(float(x_cm), float(y_cm))

    def bbox_to_ground(self, bbox: BBox) -> GroundPoint:
        """แปลงกรอบ ``[x1, y1, x2, y2]`` จาก decisions.json เป็นตำแหน่งบนพื้น

        ใช้ "ขอบล่างกึ่งกลางกรอบ" เป็นตัวแทนตำแหน่ง เพราะเป็นจุดที่ใกล้เคียงกับจุดที่
        ต้นไม้สัมผัสพื้นมากที่สุด ถ้าใช้จุดกึ่งกลางกรอบจะได้ตำแหน่งที่ไกลกว่าความจริง
        เพราะกึ่งกลางกรอบอยู่ลอยเหนือพื้น
        """
        x1, y1, x2, y2 = bbox
        bottom_center = ((x1 + x2) / 2.0, max(y1, y2))
        return self.pixel_to_ground(bottom_center)

    def save(self, path: str | Path) -> None:
        """เก็บ homography ลงไฟล์ จะได้ไม่ต้องวัดจุดอ้างอิงใหม่ทุกครั้ง"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "units": "cm",
            "frame": "robot_relative_ground_plane",
            "note": "ใช้ได้เฉพาะการติดตั้งกล้องแบบที่คาลิเบรตไว้เท่านั้น",
            "matrix": self.matrix.tolist(),
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "GroundPlane":
        """อ่าน homography ที่เคยเก็บไว้"""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(np.array(payload["matrix"], dtype=np.float64))


def annotate_decisions(decisions: dict, plane: GroundPlane) -> dict:
    """เติมพิกัดเซนติเมตรบนพื้นเข้าไปในผลลัพธ์ที่อ่านมาจาก ``decisions.json``

    คืนค่าเป็น dict ชุดใหม่ ไม่แก้ของเดิม ทุกรายการตรวจจับจะได้คีย์ ``ground``
    เพิ่มเข้ามา ส่วนกฎตัดสินใจและ ``actuation_authorized`` ไม่ถูกแตะต้อง
    ฟังก์ชันนี้ **ไม่** เปลี่ยนคำแนะนำใด ๆ เพียงเพิ่มข้อมูลระยะเท่านั้น
    """
    annotated = json.loads(json.dumps(decisions))
    annotated["ground_frame"] = "robot_relative_cm"
    annotated["ground_frame_note"] = (
        "พิกัดเทียบกับตัวหุ่นในเฟรมนั้น ไม่ใช่พิกัดของสวน "
        "ยังไม่มี localization จึงนำไปสะสมเป็นแผนที่ไม่ได้"
    )
    for frame in annotated.get("frames", []):
        for detection in frame.get("detections", []):
            detection["ground"] = plane.bbox_to_ground(tuple(detection["bbox"])).to_dict()
    return annotated


if __name__ == "__main__":
    print(__doc__)
    print(
        "ไฟล์นี้ยังเป็นโครงของ Phase 2 ยังไม่ได้ต่อกับ detect.py\n"
        "ขั้นตอนถัดไปคือถ่ายรูปจุดอ้างอิง 4 จุดตามที่อธิบายไว้ด้านบน "
        "แล้วจดพิกเซลกับระยะจริงมาใส่ใน GroundPlane.from_reference_points"
    )
