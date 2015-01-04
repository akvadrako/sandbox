
# ASPATH BUFFER
truncate aspath_buffer;
alter table aspath_buffer ENGINE = MyISAM delay_key_write = 1;
create index origin_path on aspath_buffer(origin_as, aspath(15));

# ROUTING ENTRY BUFFER
truncate routing_entry_buffer;
alter table routing_entry_buffer ENGINE = MyISAM delay_key_write = 1;
create index prefix_peer on routing_entry_buffer(prefix, peer);

# ATTRIBUTES BUFFER
truncate attributes_buffer;
alter table attributes_buffer ENGINE = MyISAM delay_key_write = 1;
create index aggr_community on attributes_buffer(aggr_as, community(20));

# RIB BUFFER
truncate rib_buffer;
alter table rib_buffer ENGINE = MyISAM delay_key_write = 1;

# CLEANUP ROUTING ENTRIES DUE TO BAD ATTRIBUTES
delete from routing_entry using routing_entry
    left outer join attributes
    on attributes.id = attributes
    where attributes IS NOT NULL and attributes.id IS NULL;

# ROUTING ENTRY
drop index routing_entry_attributes_idx ON routing_entry;
drop index routing_entry_prefix_idx ON routing_entry;
create index prefix_attr on routing_entry(prefix, attributes);

# ASPATH
drop index aspath_idx on aspath;
drop index aspath_origin_as_idx on aspath;
create index origin_path on aspath(origin_as, aspath(15));

# ATTRIBUTES
drop index attributes_next_hop_idx on attributes;
drop index attributes_aggr_as_idx on attributes;
drop index attributes_community_idx on attributes;
create index most_columns ON attributes(origin, med, aggr_addr, community(10));
