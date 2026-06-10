from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, nullable=True)
    query = Column(String)
    response = Column(String)
    latency_total_ms = Column(Integer)
    latency_stt_ms = Column(Integer, default=0)
    latency_retrieval_ms = Column(Integer, default=0)
    latency_llm_ms = Column(Integer, default=0)
    latency_tts_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    eval_score = relationship("EvalScore", back_populates="query_log", uselist=False)

class EvalScore(Base):
    __tablename__ = "eval_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    query_log_id = Column(String, ForeignKey("query_logs.id"))
    faithfulness = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    citation_accuracy = Column(Float, nullable=True)
    
    query_log = relationship("QueryLog", back_populates="eval_score")
