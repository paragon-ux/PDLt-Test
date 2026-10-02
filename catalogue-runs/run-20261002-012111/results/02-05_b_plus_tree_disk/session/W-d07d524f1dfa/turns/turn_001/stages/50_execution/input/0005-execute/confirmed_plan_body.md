DEFINE B+ tree class with configurable order default 4
DESIGN internal node structure holding routing keys only
DESIGN leaf node structure storing values exclusively
LINK leaf nodes via doubly-linked list
IMPLEMENT INSERT operation inserting key/value into appropriate leaf node and handling node splits
IMPLEMENT SEARCH operation locating key by traversing internal nodes to leaf node
IMPLEMENT RANGE_SCAN operation iterating leaf nodes from lo to hi and collecting values
IMPLEMENT SERIALIZE operation converting tree into page-level representation
IMPLEMENT DESERIALIZE operation reconstructing tree from serialized pages
DEVELOP test suite covering insertion splits, range-scan correctness, and serialize/deserialize round-trip fidelity
RUN test suite and record outcomes
