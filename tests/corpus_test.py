"""
Pytest tests for the single instance of Corpus in corpus.py
"""

from bot.helpers.corpus import corpus


def test_corpus():
    """Test sentence generation"""
    corpus.generate_sentence()
    # Test with strings from the corpus keys
    seeds = ["Welcome, Aristocrat,",
             "You are",
             "Ask a",
             "What are",
             "Get Pax",
             "Return to",
             "You are",
             "You chance",
             "Whilom, when",
             "when Salum",
             '"but, take',
             "Ol' Uri",
             "Russell, Gödel,",
             "in my",
             "systems' inference",
             "Curious. ~",
             "~ ~",
             "vacant flats.",
             "palings a",
             "wide passage",
             "passage opens",
             "opens into",
             ]
    for seed in seeds:
        assert len(corpus.generate_sentence(seed=seed)) > len(seed)


def test_secret_generation():
    """Test generation of Ruin of House Isner secret"""
    corpus.generate_sentence(seed="isner test")
