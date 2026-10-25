"""Tests for Google Photos date-clustering and burst shot detection."""

import pytest
from neatworkspace.photos_scanner import PhotosScanner, PhotoItem


def test_photo_album_clustering():
    p1 = PhotoItem(
        id="p1",
        filename="IMG_20261025.jpg",
        mime_type="image/jpeg",
        creation_time="2026-10-25T14:30:00Z"
    )
    p2 = PhotoItem(
        id="p2",
        filename="IMG_20260510.jpg",
        mime_type="image/jpeg",
        creation_time="2026-05-10T09:15:00Z"
    )

    assert p1.target_album_name == "NeatPhotos 2026 10-October"
    assert p2.target_album_name == "NeatPhotos 2026 05-May"

    scanner = PhotosScanner(photos_service=None)
    clusters = scanner.cluster_by_album([p1, p2])

    assert len(clusters) == 2
    assert "NeatPhotos 2026 10-October" in clusters
    assert "NeatPhotos 2026 05-May" in clusters


def test_photo_burst_detection():
    # 3 photos taken within 1 second with identical resolution = burst
    b1 = PhotoItem(id="1", filename="IMG_1.jpg", mime_type="image/jpeg", creation_time="2026-10-25T12:00:00Z", width=4000, height=3000)
    b2 = PhotoItem(id="2", filename="IMG_2.jpg", mime_type="image/jpeg", creation_time="2026-10-25T12:00:01Z", width=4000, height=3000)
    b3 = PhotoItem(id="3", filename="IMG_3.jpg", mime_type="image/jpeg", creation_time="2026-10-25T12:00:02Z", width=4000, height=3000)
    # Photo taken 20 minutes later = not burst
    b4 = PhotoItem(id="4", filename="IMG_4.jpg", mime_type="image/jpeg", creation_time="2026-10-25T12:20:00Z", width=4000, height=3000)

    scanner = PhotosScanner(photos_service=None)
    bursts = scanner.detect_burst_duplicates([b1, b2, b3, b4], threshold_seconds=2)

    assert len(bursts) == 1
    assert len(bursts[0]) == 3
    assert bursts[0][0].id == "1"
    assert bursts[0][2].id == "3"


def test_photo_screenshot_detection():
    p = PhotoItem(id="1", filename="Screenshot_20261025.png", mime_type="image/png", creation_time="2026-10-25T10:00:00Z")
    assert p.is_screenshot is True
