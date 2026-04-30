from __future__ import annotations

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DocumentProcessORM(Base):
    __tablename__ = "document_processes"

    process_id: Mapped[str] = mapped_column(Text, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    consistency_result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class TradeChainORM(Base):
    __tablename__ = "trade_chains"

    chain_id: Mapped[str] = mapped_column(Text, primary_key=True)
    case_no: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class TradeDocumentORM(Base):
    __tablename__ = "trade_documents"

    document_id: Mapped[str] = mapped_column(Text, primary_key=True)
    chain_id: Mapped[str] = mapped_column(ForeignKey("trade_chains.chain_id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    doc_no: Mapped[str | None] = mapped_column(Text)
    issue_date: Mapped[str | None] = mapped_column(Text)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_process_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_processes.process_id", ondelete="SET NULL")
    )
    normalized_payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class DocumentComparisonORM(Base):
    __tablename__ = "document_comparisons"

    comparison_id: Mapped[str] = mapped_column(Text, primary_key=True)
    chain_id: Mapped[str] = mapped_column(ForeignKey("trade_chains.chain_id", ondelete="CASCADE"), nullable=False)
    base_document_id: Mapped[str] = mapped_column(
        ForeignKey("trade_documents.document_id", ondelete="CASCADE"), nullable=False
    )
    target_document_id: Mapped[str] = mapped_column(
        ForeignKey("trade_documents.document_id", ondelete="CASCADE"), nullable=False
    )
    rule_set_version: Mapped[str | None] = mapped_column(Text)
    result_status: Mapped[str] = mapped_column(Text, nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class DocumentComparisonItemORM(Base):
    __tablename__ = "document_comparison_items"

    item_id: Mapped[str] = mapped_column(Text, primary_key=True)
    comparison_id: Mapped[str] = mapped_column(
        ForeignKey("document_comparisons.comparison_id", ondelete="CASCADE"), nullable=False
    )
    field_path: Mapped[str] = mapped_column(Text, nullable=False)
    base_value: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[str | None] = mapped_column(Text)
    diff_type: Mapped[str] = mapped_column(Text, nullable=False)
    tolerance_rule_id: Mapped[str | None] = mapped_column(Text)
    is_acceptable: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class DocumentTypeRuleSetORM(Base):
    __tablename__ = "document_type_rule_sets"

    rule_set_id: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class DocumentTypeRuleORM(Base):
    __tablename__ = "document_type_rules"

    rule_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rule_set_id: Mapped[str] = mapped_column(
        ForeignKey("document_type_rule_sets.rule_set_id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    condition_type: Mapped[str] = mapped_column(Text, nullable=False)
    condition_key: Mapped[str] = mapped_column(Text, nullable=False)
    condition_value: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")


class DocumentTypeInferenceLogORM(Base):
    __tablename__ = "document_type_inference_logs"
    __table_args__ = (CheckConstraint("is_overridden IN (0, 1)"),)

    evaluation_id: Mapped[str] = mapped_column(Text, primary_key=True)
    process_id: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[str] = mapped_column(Text, nullable=False)
    rule_set_version: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    final_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_overridden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, server_default="CURRENT_TIMESTAMP")
