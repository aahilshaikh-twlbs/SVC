from pinecone import Pinecone
import os
import json
import numpy as np
import csv
import re
from dotenv import load_dotenv
load_dotenv()

pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
index = pc.Index("ffmpeg_tests")

def fetch_segment_embeddings_for_version(
    asset_id: str,
    version_id: str,
    index,
    embedding_scope: str = "clip"
):
    """
    Fetch all segment embeddings for a single version of an Iconik asset.

    :param iconik_id: The Iconik asset ID (same for all versions).
    :param version_id: The specific version ID in Iconik.
    :param index: Pinecone Index object.
    :param embedding_scope: 'clip' or 'video'. Typically 'clip' for segment-level.
    :return: A list of dicts like:
       [
         {
           'start_offset_sec': 0.0,
           'end_offset_sec': 2.0,
           'embedding': [float, float, ...]
         },
         ...
       ]
       sorted by start_offset_sec ascending.
    """

    # We can do a filter-based query for all segments for this version.
    # Use a 'dummy' vector to query, but set top_k high and rely on the filter.
    query_filter = {
        "iconik_id": asset_id,
        "version_id": version_id,
        "embedding_scope": embedding_scope
    }

    # Use a sufficiently large top_k so we get all segments.
    # (If you store thousands of segments, adjust accordingly.)
    results = index.query(
        vector=[0]*1024,            # or whatever your embedding size is
        filter=query_filter,
        top_k=9999,
        include_values=True,
        include_metadata=True
    )
    segments = []
    if results and results.matches:
        for match in results.matches:
            metadata = match.metadata
            if not metadata:
                continue
            seg = {
                "start_offset_sec": float(metadata.get("start_offset_sec", 0)),
                "end_offset_sec": float(metadata.get("end_offset_sec", 0)),
                "embedding": match.values  # the actual embedding vector
            }
            segments.append(seg)

    # Sort by start_offset_sec ascending
    segments.sort(key=lambda s: s["start_offset_sec"])
    return segments

def compare_segments_by_time(
        segments_v1,
        segments_v2,
        threshold=0.03,
        distance_metric="cosine",
        csv_output_path = "/Users/simonlecointe/Desktop/segment_distances.csv"
):
    """
    Compare two lists of segment embeddings (v1 vs v2) for the same asset,
    but different versions. Identify which segments differ based on a threshold.

    Each list entry is dict:
      {
        'start_offset_sec': float,
        'end_offset_sec': float,
        'embedding': list/np.ndarray
      }

    :param segments_v1: List of segment dicts (for version 1).
    :param segments_v2: List of segment dicts (for version 2).
    :param threshold: Distance above which we consider the segment "changed".
    :param distance_metric: 'cosine' or 'euclidean'.
    :return: A list of dicts describing where differences occur:
      [
        {
          "start_sec": 0.0,
          "end_sec": 2.0,
          "distance": 0.45
        },
        ...
      ]
    """

    # Convert the lists into dictionaries keyed by start_offset_sec,
    # so we can easily match them.
    # (We round to handle floating precision issues, e.g., 0 vs 0.0001)
    def keyfunc(s):
        return round(s["start_offset_sec"], 2)

    dict_v1 = {keyfunc(seg): seg for seg in segments_v1}
    dict_v2 = {keyfunc(seg): seg for seg in segments_v2}

    # Combine all possible start times
    all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
    differing_segments = []
    all_segments_info = []  # Will hold every segment comparison

    for k in sorted(all_keys):
        seg1 = dict_v1.get(k)
        seg2 = dict_v2.get(k)

        if not seg1 or not seg2:
            # If both seg1 and seg2 are None (should be rare but let's handle it):
            if seg1 is None and seg2 is None:
                continue  # or do something else appropriate

            # Otherwise, pick which one is not None.
            valid_seg = seg1 if seg1 is not None else seg2

            # Safely get the start_sec and end_sec
            start_sec = valid_seg["start_offset_sec"]
            end_sec = valid_seg["end_offset_sec"]

            # Add the info
            all_segments_info.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "distance": float('inf')
            })

            # Also treat it as a difference
            differing_segments.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "distance": float('inf')
            })

            continue

        # Convert to numpy for distance calc
        v1 = np.array(seg1["embedding"], dtype=np.float32)
        v2 = np.array(seg2["embedding"], dtype=np.float32)

        if distance_metric == "cosine":
            dist = cosine_distance(v1, v2)
            print(dist)
        else:
            dist = euclidean_distance(v1, v2)

        all_segments_info.append({
            "start_sec": seg1["start_offset_sec"],
            "end_sec": seg1["end_offset_sec"],
            "distance": float(dist)
        })
        # Cast dist to float to avoid np.float32 serialization error
        dist_val = float(dist)
        if dist_val > threshold:
            differing_segments.append({
                "start_sec": seg1["start_offset_sec"],
                "end_sec": seg1["end_offset_sec"],
                "distance": dist_val
            })

    # -- WRITE the CSV for all segments (below or above threshold) --
    with open(csv_output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["start_sec", "end_sec", "distance"])
        writer.writeheader()
        for row in all_segments_info:
            writer.writerow(row)

    return differing_segments


def cosine_distance(v1, v2):
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    similarity = dot / (norm1 * norm2)
    return 1.0 - similarity


def euclidean_distance(v1, v2):
    return float(np.linalg.norm(v1 - v2))


def pinpoint_segment_differences(
    asset_id: str,
    version_id1: str,
    version_id2: str,
    index,
    distance_threshold: float = 0.03,
    embedding_scope: str = "clip"
):
    """
    Retrieve all 2-second embeddings from Pinecone for (iconik_id, version_id1)
    and (iconik_id, version_id2), compare each segment, and return a list of
    the segments that differ above the given threshold.

    :return: A list of differing segments. E.g.:
      [
        {"start_sec": 0.0, "end_sec": 2.0, "distance": 0.47},
        {"start_sec": 10.0, "end_sec": 12.0, "distance": 0.41},
        ...
      ]
    """

    # 1) Fetch segments
    segments_v1 = fetch_segment_embeddings_for_version(
        asset_id=asset_id,
        version_id=version_id1,
        index=index,
        embedding_scope=embedding_scope
    )
    segments_v2 = fetch_segment_embeddings_for_version(
        asset_id=asset_id,
        version_id=version_id2,
        index=index,
        embedding_scope=embedding_scope
    )

    # 2) Compare
    differing_segments = compare_segments_by_time(segments_v1, segments_v2, threshold=distance_threshold,
                                                  distance_metric="cosine", csv_output_path = "/Users/simonlecointe/Desktop/segment_distances_v3.csv")

    return differing_segments

def get_version_id_for_label(asset_dict, label):
        """
        asset_dict is the dictionary returned by ik.get_asset(...).
        label is something like 'V1', 'V4', etc.
        Returns the actual version ID (the 'id' field in the versions list).
        """
        # Extract the list of versions.
        versions_list = asset_dict["versions"]

        # Sort them by date_created ascending
        sorted_versions = sorted(versions_list, key=lambda v: v["date_created"])
        print("Sorted Versions:", sorted_versions)
        # Convert user-friendly label "V4" -> integer 4 -> zero-based index 3
        match = re.match(r"V(\d+)", label)
        if not match:
            raise ValueError(f"Version label '{label}' is not in the format 'V<number>'")

        version_number = int(match.group(1))  # e.g. "4"
        zero_index = version_number - 1  # e.g. 4 -> 3

        if zero_index < 0 or zero_index >= len(sorted_versions):
            raise ValueError(
                f"Requested version '{label}' out of range. This asset has {len(sorted_versions)} versions.")

        # Retrieve the actual version ID
        actual_version_id = sorted_versions[zero_index]["id"]
        return actual_version_id

def lambda_handler(event, context):


    body = json.loads(event["body"])
    asset_id = body["asset_ids"][0]
    source_label = body["metadata_values"]["TL_SOURCE_VERSION"]["field_values"][0]["value"]
    target_label = body["metadata_values"]["TL_TARGET_VERSION"]["field_values"][0]["value"]
    segment_metadata_view_id = "d50441a6-dd01-11ef-b04a-a67d0c7f3087"
    asset = ik.get_asset(asset_id)

    source_version_id = get_version_id_for_label(asset, source_label)
    target_version_id = get_version_id_for_label(asset, target_label)

    print("Source version ID:", source_version_id)
    print("Target version ID:", target_version_id)

    differences = pinpoint_segment_differences(
        asset_id=asset_id,
        version_id1=source_version_id,
        version_id2=target_version_id,
        index=index,  # your Pinecone index
        distance_threshold=0.20,
        embedding_scope="clip"   # or "video" if you used single embeddings
    )

    if not differences:
        print("No significant differences found between versions!")
    else:
        for diff in differences:
            print(f"[{diff['start_sec']} - {diff['end_sec']}s] difference={diff['distance']:.3f}")

            start_ms = int(diff['start_sec'] * 1000)  # Convert start time to ms
            end_ms = int(diff['end_sec'] * 1000)

            # 1) Create a segment in Iconik
            create_segment_result = ik.create_asset_segment(
                asset_id=asset_id,
                view_id=segment_metadata_view_id,  # The metadata view you use for segments
                start=start_ms,
                end=end_ms,
                color="red",  # Set color to red
                segment_type="GENERIC",  # or "SHOT", "SCENE", etc. depending on your use
                text="Difference found",
                version_id=target_version_id# The "name"/label on the segment
            )

            segment_id = create_segment_result["id"]
            print(f"Created segment id={segment_id} for difference={diff['distance']:.3f}")

            # 2) Build the metadata payload
            #    In this example, we're adding:
            #       TL_VERSION_COMPARAISON = "Difference found"
            #       TL_DISTANCE           = <distance numeric value>
            segment_meta = {
                "metadata_values": {
                    "TL_VERSION_COMPARISON": {
                        "field_values": [
                            {"value": "Difference found"}
                        ]
                    },
                    "TL_DISTANCE": {
                        "field_values": [
                            {"value": str(diff["distance"])}
                        ]
                    }
                }
            }
            # 3) Add the metadata to the newly created segment
            ik.add_metadata_to_segment(
                asset_id=asset_id,
                segment_id=segment_id,
                view_id=segment_metadata_view_id,
                metadata_json=segment_meta
            )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "differences": differences
        })
    }




event = {
    'body': '''
    {
      "user_id": "8951f88e-7ff0-11ef-b7ae-4664fc99c07f",
      "system_domain_id": "86729aec-7ff0-11ef-a5cc-2e53d2c327db",
      "context": "ASSET",
      "action_id": "239f8c18-d9d7-11ef-aa69-ea99ee0ee558",
      "asset_ids": [
        "57a74a7e-dffd-11ef-ac40-72ad9f589024"
      ],
      "collection_ids": [],
      "saved_search_ids": [],
      "metadata_view_id": "156883b8-dab1-11ef-beb8-f617c15dd4ee",
      "metadata_values": {
        "TL_SOURCE_VERSION": {
          "field_values": [
            {
              "value": "V1"
            }
          ]
        },
        "TL_TARGET_VERSION": {
          "field_values": [
            {
              "value": "V2"
            }
          ]
        }
      },
      "date_created": "2025-01-27T19:36:59.883776"
    }
    '''
}

lambda_handler(event, context=None)
