from datetime import datetime
from typing import List, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func

from evoflow_db.base import Base


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
    reactor_config_json: Mapped[dict[str, Any]] = mapped_column()
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Experiment
    experiment: Mapped["Experiment"] = relationship(back_populates="reactor_configs")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


class ExperimentState(Base):
    __tablename__ = "experiment_state"
    state_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.experiment_id"), nullable=True
    )
    inc_od: Mapped[float] = mapped_column(nullable=True)
    inc_tot_dil: Mapped[float] = mapped_column(nullable=True)
    inc_temp: Mapped[float] = mapped_column(nullable=True)
    lagoon_temp: Mapped[float] = mapped_column(nullable=True)
    lagoon_flow_rate: Mapped[float] = mapped_column(nullable=True)
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Experiment
    experiment: Mapped["Experiment"] = relationship(back_populates="experiment_states")
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


class ExperimentConfig(Base):
    __tablename__ = "experiment_config"
    exp_config_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiment.experiment_id"))
    exp_config_json: Mapped[dict[str, Any]] = mapped_column()
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
    timestamp: Mapped[int] = mapped_column()

    # Many-to-One relationship with Reactor
    reactor: Mapped["Reactor"] = relationship(back_populates="experiments")
    # One-to-Many relationships with ReactorConfig, ReactorState, and ExpConfig
    reactor_configs: Mapped[List["ReactorConfig"]] = relationship(
        back_populates="experiment"
    )
    experiment_states: Mapped[List["ExperimentState"]] = relationship(
        back_populates="experiment"
    )
    exp_configs: Mapped[List["ExperimentConfig"]] = relationship(
        back_populates="experiment"
    )
    inserted_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())
