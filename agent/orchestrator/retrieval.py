"""Một đường truy xuất duy nhất, dùng chung bởi node và script hiệu chỉnh.

Trước khi có file này, `scripts/check_retrieval.py` đo truy xuất bằng **câu hỏi thô**
trong khi node chạy **câu đã mở rộng** kèm một lượt dự phòng. Nghĩa là công cụ hiệu
chỉnh ngưỡng đang đo một hệ thống khác với hệ thống thật: nó có thể xanh trong khi
production từ chối câu hỏi hợp lệ, và ngược lại.

Một ngưỡng chỉ có ý nghĩa khi nó được đo trên đúng thứ sẽ chạy.
"""

from __future__ import annotations

from agent.orchestrator.router import route
from agent.schemas import Hit
from agent.tools.search_knowledge import search_knowledge


def retrieve_for(message: str) -> list[Hit]:
    """Truy xuất bằng chứng cho một câu hỏi thô, đúng như orchestrator làm.

    Câu mở rộng dùng để TÌM đoạn văn; chữ gốc của người hỏi dùng để CHẤM điểm tin
    cậy — mở rộng bơm từ vựng lấy từ chính corpus, nên chấm điểm trên nó là đo xem
    ta mở rộng khéo tới đâu, không phải đo xem ta có biết câu trả lời hay không.
    """
    ruled = route(message)
    query = ruled[1] if ruled else message

    hits = search_knowledge(query, score_query=message)
    if not hits and ruled:
        # Một luật viết tay khớp là bằng chứng mạnh rằng câu hỏi đúng chủ đề — mạnh
        # hơn phỏng đoán của model. Khi đó, chấm điểm trên bản dịch của chính luật.
        hits = search_knowledge(query, score_query=query)
    return hits
