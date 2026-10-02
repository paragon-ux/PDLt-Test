DEFINE LFUCache class with constructor(capacity)
INITIALIZE key_to_node hashmap
INITIALIZE freq_to_nodes hashmap of ordered collections
INITIALIZE min_frequency variable set to 0
IMPLEMENT get(key) method
  IF key not present THEN RETURN -1
  CALL update_node_frequency(node)
  RETURN node.value
IMPLEMENT put(key, value) method
  IF capacity is 0 THEN EXIT
  IF key present THEN UPDATE node.value and CALL update_node_frequency(node)
  ELSE
    IF cache size equals capacity THEN CALL evict_least_frequently_used()
    INSERT new node with frequency 1 into key_to_node and freq_to_nodes[1]
    SET min_frequency to 1
IMPLEMENT update_node_frequency(node) helper
  REMOVE node from freq_to_nodes[node.frequency]
  IF freq_to_nodes[node.frequency] is empty AND node.frequency equals min_frequency THEN INCREMENT min_frequency
  INCREMENT node.frequency
  ADD node to freq_to_nodes[node.frequency] as most recent
IMPLEMENT evict_least_frequently_used() helper
  SELECT LRU node from freq_to_nodes[min_frequency]
  REMOVE selected node from key_to_node and freq_to_nodes[min_frequency]
ENSURE all operations maintain O(1) average time complexity
CREATE self-contained test suite
  DEFINE test case verifying basic put and get operations
  DEFINE test case verifying capacity eviction of least frequently used key
  DEFINE test case verifying frequency count increments on get and put
  DEFINE test case verifying LRU tie-breaking among keys with equal minimum frequency
  EXECUTE each test case and VERIFY expected cache state and returned values
REPORT test suite outcomes
