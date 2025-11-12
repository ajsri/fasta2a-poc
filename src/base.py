# src/base.py
from fasta2a.schema import Message
from pydantic import BaseModel
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage

storage = InMemoryStorage()
broker = InMemoryBroker()

Context = list[Message]
