"""classes to keep track of biLouvian community result, and to calculate similarity between coclusters"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Set, Any
from datetime import datetime

__all__ = ["VertexType", "ClusterItem", "CoClusterItem", "CommunityResult", "CommunityResultTime"]


class VertexType(str, Enum):
    """Vertex type can only be `V1` or `V2`"""

    V1 = "V1"
    V2 = "V2"

    def __new__(cls, value):
        if value not in ["V1", "V2"]:
            raise ValueError("vertex type can only be `V1` or `V2`")
        return super().__new__(cls, value)

    def getother(self: "VertexType") -> "VertexType":
        """Return the other vertex type"""
        if self == VertexType.V1:
            return VertexType.V2
        elif self == VertexType.V2:
            return VertexType.V1


@dataclass
class ClusterItem:
    """class of keeping track of cluster information"""

    community_id: int
    member: Set[Any]
    type: VertexType | None = None  # type of the cluster

    def __hash__(self) -> int:
        return hash(str(self.community_id) + self.type)

    def __repr__(self) -> str:
        if self.type == VertexType.V1:
            return str(self.member)
        else:
            return str(list(self.member)[0:5] + ["..."])


@dataclass
class CoClusterItem:
    """class of keeping track of co-cluster information"""

    cocluster_id: int
    first: ClusterItem
    second: ClusterItem

    def __hash__(self) -> int:
        return hash((self.cocluster_id, self.first, self.second, self.first, self.second))

    def similarity_first(self, other: "CoClusterItem") -> float:
        """Calculate the similarity between two coclusters based on the first vertex type"""
        # overlap over union of the first vertex type
        first_overlap = len(self.first.member.intersection(other.first.member))
        first_union = len(self.first.member.union(other.first.member))
        return first_overlap / first_union

    def similarity_second(self, other: "CoClusterItem") -> float:
        """Calculate the similarity between two coclusters based on the second vertex type"""
        # overlap over union of the second vertex type
        second_overlap = len(self.second.member.intersection(other.second.member))
        second_union = len(self.second.member.union(other.second.member))
        return second_overlap / second_union

    def similarity(self, other: "CoClusterItem") -> float:
        """Calculate the similarity between two coclusters"""
        first_similarity = self.similarity_first(other)
        second_similarity = self.similarity_second(other)
        # return the average of the two similarities
        return (first_similarity + second_similarity) / 2


@dataclass
class CommunityResult:
    """class of keeping track of community detection result"""

    clusters: Set[ClusterItem]
    coclusters: Set[CoClusterItem]


@dataclass
class CommunityResultTime:
    """class of keeping track of community detection result with time"""

    community: CommunityResult
    time_from: datetime
    time_to: datetime
    country: str = "all"
    biLouvian_order: int = 1


def test_VertexType():
    assert VertexType("V1") == VertexType.V1
    assert VertexType("V2").getother() == VertexType.V1


def test_CoclusterItem():
    """test the similarity function"""
    cluster11 = ClusterItem(1, {"A", "B", "C"})
    cluster12 = ClusterItem(2, {"D", "E", "F"})
    cluster21 = ClusterItem(3, {1, 2, 3})
    cluster22 = ClusterItem(4, {4, 5, 6})
    cocluster1 = CoClusterItem(1, cluster11, cluster21)
    cocluster2 = CoClusterItem(2, cluster12, cluster22)
    assert cocluster1.similarity(cocluster2) == 0.0
    cocluster3 = CoClusterItem(3, cluster11, cluster22)
    assert cocluster1.similarity(cocluster3) == 0.5
