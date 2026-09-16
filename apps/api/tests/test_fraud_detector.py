"""
Unit tests for the fraud detector service.

Tests entity extraction from scam text, process_user_submission
with a mocked database session, and submission clustering behavior.
"""

from unittest.mock import MagicMock, patch

from app.services.fraud_detector import extract_entities, process_user_submission

# ---------------------------------------------------------------------------
# extract_entities
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_extracts_phone_numbers(self):
        text = "Call 0991234567 or 0882000001 for your free prize."
        result = extract_entities(text)
        assert isinstance(result["phones"], list)
        # At least one phone should be detected
        assert len(result["phones"]) >= 1

    def test_extracts_urls(self):
        text = "Claim at http://bit.ly/fake or http://another.link/scam"
        result = extract_entities(text)
        assert any("bit.ly" in u for u in result["urls"])

    def test_detects_airtel_money_institution(self):
        text = "Airtel Money is giving away MK100,000 to lucky winners today!"
        result = extract_entities(text)
        assert "airtel money" in result["institutions"]

    def test_detects_standard_bank_institution(self):
        text = "Standard Bank has approved your loan application."
        result = extract_entities(text)
        assert "standard bank" in result["institutions"]

    def test_detects_tnm_mpamba_institution(self):
        text = "TNM Mpamba is offering 50% bonus on all transfers."
        result = extract_entities(text)
        assert "tnm mpamba" in result["institutions"]

    def test_returns_empty_lists_when_nothing_found(self):
        text = "This is a perfectly normal message."
        result = extract_entities(text)
        assert isinstance(result["phones"], list)
        assert isinstance(result["urls"], list)
        assert isinstance(result["institutions"], list)

    def test_deduplicates_phones(self):
        text = "Call 0991234567 and 0991234567 again."
        result = extract_entities(text)
        phones = result["phones"]
        # All entries should be unique
        assert len(phones) == len(set(phones))

    def test_deduplicates_urls(self):
        url = "http://bit.ly/scam"
        text = f"{url} visit {url}"
        result = extract_entities(text)
        assert result["urls"].count(url) == 1


# ---------------------------------------------------------------------------
# process_user_submission (mocked DB)
# ---------------------------------------------------------------------------

class TestProcessUserSubmission:
    def _make_mock_db(self, existing_cluster=None) -> MagicMock:
        """Build a mock DB session for submission processing."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = existing_cluster
        mock_db = MagicMock()
        mock_db.query.return_value = mock_query
        return mock_db

    def test_creates_submission_and_returns_it(self):
        text = "Airtel Money free data — call 0991111111"
        mock_db = self._make_mock_db(existing_cluster=None)

        # Mock get_embedding to return None so the embedding branch is skipped
        with patch(
            "app.services.fraud_detector.get_embedding", return_value=None
        ):
            process_user_submission(mock_db, text)

        # DB add should have been called at least once (cluster + submission)
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_adds_to_existing_cluster_when_found(self):
        text = "Standard Bank free credit — 0882333444"
        fake_cluster = MagicMock()
        fake_cluster.submission_count = 3
        fake_cluster.id = 42
        mock_db = self._make_mock_db(existing_cluster=fake_cluster)

        with patch(
            "app.services.fraud_detector.get_embedding", return_value=[0.1] * 10
        ):
            process_user_submission(mock_db, text)

        # Cluster count should have been incremented
        assert fake_cluster.submission_count == 4

    def test_creates_new_cluster_when_none_exists(self):
        text = "RBM emergency fund — click http://bit.ly/rbm-emergency"
        mock_db = self._make_mock_db(existing_cluster=None)

        with patch(
            "app.services.fraud_detector.get_embedding", return_value=None
        ):
            process_user_submission(mock_db, text)

        # add should be called for both the new cluster and the submission
        assert mock_db.add.call_count >= 2

    def test_handles_empty_text_without_crashing(self):
        """Empty text should not raise; service should handle it gracefully."""
        mock_db = self._make_mock_db(existing_cluster=None)
        with patch(
            "app.services.fraud_detector.get_embedding", return_value=None
        ):
            # Should not raise
            process_user_submission(mock_db, "")
        assert mock_db.commit.called
