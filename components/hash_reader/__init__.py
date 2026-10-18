import os
import streamlit.components.v1 as components

_hash_reader = components.declare_component(
    "hash_reader",
    path=os.path.dirname(__file__)
)

def hash_reader():

    return _hash_reader(default="")
