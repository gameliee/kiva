"""classes to keep track of biLouvian community result, and to calculate similarity between coclusters"""
import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Set, Any
from datetime import datetime
import pytest

__all__ = [
    "VertexType",
    "ClusterItem",
    "CoClusterItem",
    "CommunityResult",
    "CommunityResultTime",
    "result_mutaraplus",
    "result_community",
]


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


def result_mutaraplus(prefix: str) -> float:
    """
    given a filename prefix
    find "{prefix}_ResultsModularity.txt"
    result mutara+ from the file
    if not found, return None
    """
    modularity_file = f"{prefix}_ResultsModularity.txt"
    regex = r"--- Final Murata\+ Modularity: (?P<mutaraplus>\d+\.\d+)"
    with open(modularity_file, "r") as f:
        text = f.read()

    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        mutarapluse = match.group("mutaraplus")
        return float(mutarapluse)

    return None


def result_community(prefix: str) -> CommunityResult:
    comm_regex = r"^Community (?P<community_id>\d+)\[(?P<vertex_type>V\d+)\]: (?P<vertexes>.*)$"
    clus_regex = r"^CoCluster (?P<cocluster_id>\d+):(?P<vertex_type>V\d+)\((?P<a_id>\d+)\)-(?P<b_id>\d+)$"

    comm_file = f"{prefix}_ResultsCommunities.txt"
    clus_file = f"{prefix}_ResultsCoClusterCommunities.txt"

    with open(comm_file, "r") as f:
        text = f.read()

    clusters: List[ClusterItem] = []
    matches = re.finditer(comm_regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        community_id = match.group("community_id")
        vertex_type = match.group("vertex_type")
        vertexes = match.group("vertexes").split(", ")[0]
        vertexes = vertexes.split(",")
        cluster = ClusterItem(community_id=int(community_id), member=set(vertexes), type=VertexType(vertex_type))
        clusters.append(cluster)

    with open(clus_file, "r") as f:
        text = f.read()

    coclusters: List[CoClusterItem] = []
    matches = re.finditer(clus_regex, text, re.MULTILINE)

    # NOTE: Becareful, the cocluster could be duplicated. like this:
    # CoCluster 1:V1(1)-2
    # CoCluster 2:V2(2)-1

    for matchNum, match in enumerate(matches, start=1):
        cocluster_id = match.group("cocluster_id")
        vertex_type = match.group("vertex_type")
        a_id = match.group("a_id")
        b_id = match.group("b_id")

        # find the cluster with id a_id in clusters
        for cluster in clusters:
            if cluster.community_id == int(a_id):
                a = cluster
                break
        else:
            raise ValueError(f"cannot find cluster with id {a_id}")

        # do the same for b_id
        for cluster in clusters:
            if cluster.community_id == int(b_id):
                b = cluster
                break
        else:
            raise ValueError(f"cannot find cluster with id {b_id}")

        if VertexType(vertex_type) != "V1":
            # swap a and b
            a, b = b, a
            a_id, b_id = b_id, a_id

        # check if the cocluster (a_id, b_id) is already in the coclusters list
        for _co in coclusters:
            if _co.first.community_id == int(a_id) and _co.second.community_id == int(b_id):
                break
        else:
            # if not, add it
            cocluster = CoClusterItem(
                cocluster_id=int(cocluster_id),
                first=a,
                second=b,
            )
            coclusters.append(cocluster)

    comm_result = CommunityResult(
        clusters=set(clusters),
        coclusters=set(coclusters),
    )

    return comm_result


@pytest.fixture
def get_prefix(tmp_path) -> str:
    return str(tmp_path / "test")


@pytest.fixture
def create_mutarapluse_file(get_prefix):
    """write this result to file"""
    ret = """
    --- Phase: 1
    Initial Total Modularity: 0.562761658656241
    Iteration: 1 - Maximum Modularity Gain: 0

    --- Final Murata+ Modularity: 0.562761658656241
    """
    with open(f"{get_prefix}_ResultsModularity.txt", "w") as f:
        f.write(ret)


@pytest.fixture
def create_comm_result_file(get_prefix):
    comm = """
Community 0[V1]: Agriculture,Arts,Construction,Education,Health
Community 1[V1]: Clothing
Community 2[V1]: Entertainment,Retail,Services
Community 3[V1]: Food
Community 4[V1]: Manufacturing
Community 5[V1]: Transportation
Community 6[V1]: Wholesale
Community 7[V2]: mole333,kathy6872,william8888,jim9667,ched,joh
Community 8[V2]: leslie5099,iolaire,rand,brian3557,licitycollin
Community 9[V2]: charlie1085,edward5886,christina9245,ultron,ka
Community 10[V2]: javier3364,abinash7164,joel2322,chloe9141,lio
Community 11[V2]: theresa5035,christy4861,pamandcarroll8133,ste
Community 12[V2]: david7777,family8076,garyk,jean6946,landon281
Community 13[V2]: bezaire8653,jim9564,rajendra8312,alex7961,bri
"""
    with open(f"{get_prefix}_ResultsCommunities.txt", "w") as f:
        f.write(comm)

    cocls = """

CoCluster 1:V1(0)-9
CoCluster 2:V1(1)-10
CoCluster 3:V1(2)-7
CoCluster 4:V1(3)-8
CoCluster 5:V1(4)-13
CoCluster 6:V1(5)-12
CoCluster 7:V1(6)-11
CoCluster 8:V2(7)-2
CoCluster 9:V2(8)-3
CoCluster 10:V2(9)-0
CoCluster 11:V2(10)-1
CoCluster 12:V2(11)-6
CoCluster 13:V2(12)-5
CoCluster 14:V2(13)-4
"""
    with open(f"{get_prefix}_ResultsCoClusterCommunities.txt", "w") as f:
        f.write(cocls)


def test_result_mutaraplus(get_prefix, create_mutarapluse_file):
    assert result_mutaraplus(get_prefix) == pytest.approx(0.562761658656241)


def test_result_community(get_prefix, create_comm_result_file):
    assert result_community(get_prefix)
