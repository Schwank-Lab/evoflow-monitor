from datetime import datetime
from re import M
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from db.tables_definition.base import Base


class Reactor(Base):
    __tablename__ = "reactor"
    reactor_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column()
    network_id: Mapped[str] = mapped_column()

    # One-to-Many relationship with Experiment
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="reactor")


class ReactorConfig(Base):
    __tablename__ = "reactor_config"
    reactor_config_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.experiment_id"))
    reactor_config_json: Mapped[str] = mapped_column()
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Experiment
    experiment: Mapped["Experiment"] = relationship(back_populates="reactor_configs")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


class ReactorState(Base):
    __tablename__ = "reactor_state"
    state_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.experiment_id"), nullable=True
    )
    inc_od: Mapped[float] = mapped_column()
    inc_temp: Mapped[float] = mapped_column()
    lagoon_temp: Mapped[float] = mapped_column()
    lagoon_flow_rate: Mapped[float] = mapped_column()
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Experiment
    experiment: Mapped["Experiment"] = relationship(back_populates="reactor_state")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


class ExpConfig(Base):
    __tablename__ = "exp_config"
    exp_config_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.experiment_id"))
    exp_config_json: Mapped[str] = mapped_column()
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Experiment
    experiment: Mapped["Experiment"] = relationship(back_populates="exp_config")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


class Experiment(Base):
    __tablename__ = "experiment"
    experiment_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    reactor_id: Mapped[int] = mapped_column(ForeignKey("reactor.reactor_id"))
    name: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    end_date: Mapped[datetime] = mapped_column()
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Reactor
    reactor: Mapped["Reactor"] = relationship(back_populates="experiments")
    # One-to-Many relationships with ReactorConfig, ReactorState, and ExpConfig
    reactor_configs: Mapped[List["ReactorConfig"]] = relationship(
        back_populates="experiment"
    )
    reactor_states: Mapped[List["ReactorState"]] = relationship(
        back_populates="experiment"
    )
    exp_configs: Mapped[List["ExpConfig"]] = relationship(back_populates="experiment")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
