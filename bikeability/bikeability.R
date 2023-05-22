

#args <- commandArgs(trailingOnly = TRUE)
#cat(args, sep ="\n")
#print(args)
# Convert to numerics
#host <- args[1]
#dbname <- args[2]
#user <- args[3]
#password <- args[4]
#location  <- args[5]
#aggr_schema <- args[6]
#srid <- args[7]




host <- "vf-athene"
dbname <- "user_simon_nieland"
user <- "niel_sm"
password <- 'Samsonpg1!'
location  <- 'test_0_v10'
aggr_table <- 'sg_test_0'
aggr_schema <- 'bikeability_tests'
srid <- '4326'

library("RPostgreSQL")
library("sp")
library("rgeos")
library("rgdal")
library("dplyr")
library("ggplot2")
library("tidyr")
library("maptools")

EPSG = make_EPSG()

p4s = EPSG[which(EPSG$code == srid), "prj4"]
drv <- dbDriver("PostgreSQL")

con <- dbConnect(drv, dbname = dbname,
                 host = host, port = 5432,
                 user = user, password = password)



psqlQuery <- function(connection, queryString) {
  resultSet <- dbSendQuery(connection, queryString)
  data <- fetch(resultSet, n=-1)
  data
}



#source("utils.R")
loadSpatialTable <- function(tbl, 
                             epsg = 4326, 
                             gid = "gid", 
                             geom = "the_geom", 
                             where = "", 
                             p4s = p4s, 
                             con = con) {
  # construct database query
  query <- paste0("SELECT ", 
                  gid, 
                  ", ST_AsText(ST_Transform(", 
                  geom, 
                  ", ", 
                  as.character(epsg), 
                  ")) wkt_geom ", 
                  "FROM ", tbl, " ", 
                  where, 
                  " ORDER BY ", 
                  gid, 
                  ";")
  raw <- psqlQuery(con, query)
  row.names(raw) = raw[, 1]
  for (i in seq(nrow(raw))) {
    if (i == 1) {
      spat = readWKT(raw[i, 2], raw[i, 1], p4s)
    }
    else {
      spat = rbind(
        spat, readWKT(raw[i, 2], raw[i, 1], p4s))
    }
  }
  spat
}


toSpDF <- function(x, name="way"){  
  id <- which(colnames(x) == name)
  l <- lapply(x[, id], readWKT)
  lines_geom <- mapply(spChFIDs, l, as.character(rownames(x)))
  #rownames(x)<- x[,"osm_id"]
  
  r <- SpatialLinesDataFrame(SpatialLines(unlist(lapply(lines_geom, function(y) y@lines)), proj4string=CRS("+proj=longlat +datum=WGS84")),x[,-id])
  return(r)
}

psqlPutTable <- function(connection, schema, table, dataframe, 
                         rownames = FALSE, ...) {
  queryString = paste("SET search_path TO ", schema, "")
  dbGetQuery(connection, queryString)
  success <- dbWriteTable(connection, table, dataframe, 
                          row.names = rownames, ...)
  dbGetQuery(con, "SET search_path TO \"$user\",public")
  success
}


toSpPDF <- function(x, name="way"){  
  id <- which(colnames(x) == name)
  l <- lapply(x[, id], readWKT)
  lines_geom <- mapply(spChFIDs, l, as.character(rownames(x)))
  #rownames(x)<- x[,"osm_id"]
  
  r <- SpatialPolygonsDataFrame(SpatialPolygons(unlist(lapply(lines_geom, function(y) y@polygons)), proj4string=CRS("+proj=longlat +datum=WGS84")),x[,-id])
  return(r)
}

toSpPtDF <- function(x, name="way"){  
  id <- which(colnames(x) == name)
  l <- lapply(x[, id], readWKT)
  points.sp <- Reduce(function(a, b) spRbind(a, b), l, l[[1]])
  x_n <- rbind(x[1,], x)
  spPtDF <- SpatialPointsDataFrame(points.sp, x_n[,-id],  proj4string=CRS("+proj=longlat +datum=WGS84"))
  return(spPtDF[-1,])
}

save_gLength  <- function(x){
  if(length(x)!=0){
    return(gLength(x)) 
  }
  else{
    return(0)
  }  
}

set_utf8 = function(x){
  # Declare UTF-8 encoding on all character strings:
  for (i in 1:ncol(x)){
    if (is.character(x[, i])) Encoding(x[, i]) <- 'UTF-8'
  }
  # Same on column names:
  for (name in colnames(x)){
    Encoding(name) <- 'UTF-8'
  }
  return(x)
}







##
## Straßentypen
##
#print(streets.query)
#setwd("D:/bikeability paper/InfRad_strukturiert/MSS")

# Query, that splits and collects lenghts according to the district they are in
streets.query <-   sprintf(
    "SELECT 
    row_number() OVER () AS id,
    st_length(st_transform(st_intersection(s.geometry, b.geometry), 3857)) AS length,
    s.oneway,
    s.surface,
    s.highway,
    b.xid,
    b.area
    FROM %s.%s_streets s,    
    %s.%s_boundaries b       
    WHERE st_intersects(s.geometry, b.geometry)", aggr_schema, location, aggr_schema, location )
# Execute Query and encode to utf-8 to avoid artifacts with umlauts
streets.intersected  <- set_utf8(dbGetQuery(con, streets.query))

  

  
#streets.intersected$highway <- substring(streets.intersected$highway, 9 )
# Aggregate the lengths on district level
streets.sums <- streets.intersected %>% group_by(xid, highway, oneway) %>% summarize(length=sum(length))
boundary.xid <- streets.intersected %>% select(xid, area) %>% distinct()

# Only take oneway streets (e.g. tagged with oneway=yes)
streets.oneway <- streets.sums %>% spread(highway, length) %>% filter(oneway==TRUE)
streets.oneway[is.na(streets.oneway)] <- 0
if("motorway" %in% colnames(streets.oneway)){
}else{ streets.oneway$motorway=0}
if("trunk" %in% colnames(streets.oneway)){
}else{ streets.oneway$trunk=0}
streets.oneway <- streets.oneway %>% group_by(xid) %>% 
  summarize(motorway=sum(motorway), primary=sum(primary), secondary=sum(secondary), tertiary=sum(tertiary), 
            trunk=sum(trunk), residential=sum(residential), living_street=sum(living_street))# %>%


# Take twoway streets (e.g. tagged with oneway=no and without specific tag)
streets.twoway <- streets.sums %>% spread(highway, length) %>% filter(is.na(oneway) | oneway==FALSE)
streets.twoway[is.na(streets.twoway)] <- 0
if("motorway" %in% colnames(streets.twoway)){
}else{ streets.twoway$motorway=0}
if("trunk" %in% colnames(streets.twoway)){
}else{ streets.twoway$trunk=0}
streets.twoway <- streets.twoway %>% group_by(xid) %>% 
  summarize(motorway=sum(motorway), primary=sum(primary), secondary=sum(secondary), tertiary=sum(tertiary), 
            trunk=sum(trunk), residential=sum(residential), living_street=sum(living_street))# %>%



# Combine oneway and twowax roads and make sure that all districts are included
street.types <- boundary.xid %>% 
  left_join(streets.oneway, by=c("xid" = "xid")) %>% 
  left_join(streets.twoway, by=c("xid" = "xid"), suffix=c("_oneway", "_twoway"))
# Set all NA is to zero because a non existent road is the same as a road with length zero.
# This will cause less errors when performing mathematical operations
street.types[is.na(street.types)] <- 0

# Construct final Output table
street.types <- street.types %>% 
  mutate(
    # Count lengths of each direction
	# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!hier jeweils *2 rausmachen!!!!!!!!!!!!!!!!!!!!!
    # primary_sum=primary_oneway+primary_twoway*2, 
    # secondary_sum=secondary_oneway+secondary_twoway*2,
    # tertiary_sum=tertiary_oneway+tertiary_twoway*2,
    # residential_sum=residential_oneway+residential_twoway*2,
    # living_street_sum=living_street_oneway+living_street_twoway*2,
    # trunk_sum=trunk_oneway+trunk_twoway*2,
    # motorway_sum=motorway_oneway+motorway_twoway*2) %>%
    primary_sum=primary_oneway+primary_twoway, 
    secondary_sum=secondary_oneway+secondary_twoway,
    tertiary_sum=tertiary_oneway+tertiary_twoway,
    residential_sum=residential_oneway+residential_twoway,
    living_street_sum=living_street_oneway+living_street_twoway,
    trunk_sum=trunk_oneway+trunk_twoway,
    motorway_sum=motorway_oneway+motorway_twoway) %>%
  mutate(
    total_length = primary_sum + secondary_sum + tertiary_sum + residential_sum + trunk_sum + motorway_sum + living_street_sum
  ) %>%
  mutate(
    # Shares of road types
    primary_share=primary_sum / total_length, 
    secondary_share=secondary_sum / total_length,
    tertiary_share=tertiary_sum / total_length,
    residential_share=residential_sum / total_length,
    living_street_share=living_street_sum / total_length,
    trunk_share=trunk_sum / total_length,
    motorway_share=motorway_sum / total_length
  ) %>%
  #desity of road types
  mutate(
    primary_density=primary_sum/(1000*area),
    secondary_density=secondary_sum/(1000*area),
    tertiary_density=tertiary_sum/(1000*area),
    residential_density=residential_sum/(1000*area),
    living_street_density=living_street_sum/(1000*area),
    trunk_density=trunk_sum/(1000*area),
    motorway_density=motorway_sum/(1000*area)
  ) %>%
  mutate(
    # Calculate Index
    index = trunk_share * -5 + motorway_share * -5 + primary_share * -3 + secondary_share * -2 + tertiary_share * 1 + residential_share * 2 + living_street_share * 3
  ) %>%
  mutate(
    # Norm index
    index_norm = (index - min(index)) / (max(index) - min(index))
  ) %>%
    # share small streets
  mutate(
    small_streets_share=tertiary_share+residential_share+living_street_share
  )

street.types$small_streets_share_z <- as.numeric(scale(street.types$small_streets_share)) 

dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_street_types", aggr_schema,location) )
psqlPutTable(con, aggr_schema, sprintf("%s_street_types",location), street.types)

#######bike infrastructure


buffer.query <- sprintf("SELECT row_number() OVER () AS id,
                      buffers.xid,
                      buffers.highway,
                      Sum(ST_Length(st_intersection(buffers.geometry, cycle_track.geometry)))
                      AS length FROM %s.%s_highway_buffers buffers,       --#change prefix according to schema here
                      %s.%s_cycle_tracks cycle_track      --#change prefix according to schema here
                      WHERE st_intersects(buffers.geometry, cycle_track.geometry) AND buffers.name = cycle_track.name
                      AND (buffers.highway in ('primary', 'secondary', 'tertiary'))
                      GROUP BY buffers.xid, buffers.highway", aggr_schema,location, aggr_schema, location)
print(buffer.query)
buffer.intersected <- set_utf8(dbGetQuery(con, buffer.query))
#buffer.intersected$highway <- substring(buffer.intersected$highway, 9 )

lane.query <- sprintf("SELECT row_number() OVER () AS id,
                    p.xid, l.highway, l.oneway, COALESCE(l.highway='cycleway:right', l.highway='cycleway'),
                      Sum(ST_Length(ST_Intersection(l.geometry, p.geometry))) as length
                      FROM %s.%s_network l, %s.%s_boundaries p        
                      WHERE
                      l.highway is not null and
                      (l.cycleway =  'lane' or l.cycleway= 'lane' or l.cycleway = 'opposite_lane') and
                      ST_Intersects(p.geometry, l.geometry)
                      GROUP BY p.xid, l.highway, l.oneway, COALESCE(l.highway='cycleway:right', l.highway='cycleway')
                      ORDER BY p.xid, highway", aggr_schema,  location, aggr_schema, location)
lane.intersected <- set_utf8(dbGetQuery(con, lane.query))
#lane.intersected$highway <- substring(lane.intersected$highway, 9 )


track.query <- sprintf("SELECT row_number() OVER () AS id,
                     p.xid, l.highway, l.oneway, COALESCE(l.highway='cycleway:right', l.highway='cycleway'), 
                     Sum(ST_Length(ST_Intersection(l.geometry, p.geometry))) as length
                     FROM %s.%s_network l, %s.%s_boundaries p         --#change prefix according to schema here
                     WHERE
                     l.highway is not null and
                     (l.cycleway = 'track' or l.cycleway = 'track' or l.cycleway = 'opposite_track') and
                     ST_Intersects(p.geometry, l.geometry)
                     GROUP BY p.xid, l.highway, l.oneway, COALESCE(l.highway='cycleway:right', l.highway='cycleway') 
                     ORDER BY p.xid, highway", aggr_schema, location, aggr_schema, location)

track.intersected <- set_utf8(dbGetQuery(con, track.query))
#track.intersected$highway <- substring(track.intersected$highway, 9 )

lane.weighted <- lane.intersected %>% 
  filter(highway %in% c("primary", "secondary", "tertiary")) %>%
  mutate(length_directions = if_else(oneway == "no" | is.na(oneway), length*2,length)) %>%
  group_by(xid, highway) %>% summarise(length =sum(length_directions)) %>%
  mutate(type = "lane")

track.weighted <- track.intersected %>% 
  filter(highway %in% c("primary", "secondary", "tertiary")) %>%
  mutate(length_directions = if_else(oneway == "no" | is.na(oneway), length*2, length)) %>%
  group_by(xid, highway) %>% summarise(length =sum(length_directions)) %>%
  mutate(type = "track")

cycle_infrastructure.intersected <- buffer.intersected %>% 
  select(xid, highway, length) %>% mutate(type="buffer") %>%
  bind_rows(lane.weighted) %>%
  bind_rows(track.weighted) %>%
  unite(cycle_street_type, type, highway,  sep="_") %>%
  spread(cycle_street_type, length, fill=0)

if("buffer_primary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$buffer_primary=0
}

if("buffer_secondary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$buffer_secondary=0
}

if("buffer_tertiary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$buffer_tertiary=0
}

if("track_primary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$track_primary=0
}
if("track_secondary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$track_secondary=0
}
if("track_tertiary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$track_tertiary=0
}
if("lane_primary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$lane_primary=0
}
if("lane_secondary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$lane_secondary=0
}
if("lane_tertiary" %in% colnames(cycle_infrastructure.intersected)){
}else{ cycle_infrastructure.intersected$lane_tertiary=0
}

cycle_infrastructure.types <- street.types %>% 
  left_join(cycle_infrastructure.intersected, by=c("xid" = "xid")) 
cycle_infrastructure.types[is.na(cycle_infrastructure.types)] <-0
cycle_infrastructure.types <- cycle_infrastructure.types %>%
  mutate(
    # Calculate cumulated length of cycling infrastructure along streets
    buffer_2_sum = buffer_primary + buffer_secondary,
    buffer_3_sum = buffer_primary + buffer_secondary + buffer_tertiary,
    lane_2_sum = lane_primary + lane_secondary,
    lane_3_sum = lane_primary + lane_secondary + lane_tertiary,
    track_2_sum = track_primary + track_secondary,
    track_3_sum = track_primary + track_secondary + track_tertiary
  ) %>%
  mutate(
    # Simple Shares
    share_prim_track = track_primary / primary_sum,
    share_sec_track = track_secondary / secondary_sum,
    share_ter_track = track_tertiary / tertiary_sum,
    
    share_prim_lane = lane_primary / primary_sum,
    share_sec_lane = lane_secondary / secondary_sum,
    share_ter_lane = lane_tertiary / tertiary_sum,
    
    share_prim_buffer = buffer_primary / primary_sum,
    share_sec_buffer = buffer_secondary / secondary_sum,
    share_ter_buffer = buffer_tertiary / tertiary_sum,
    
    # Calculate share
    share_2 = (track_2_sum + lane_2_sum) / (primary_sum + secondary_sum),
    share_3 = (track_3_sum + lane_3_sum) / (primary_sum + secondary_sum + tertiary_sum),
    # Take seperate cycle tracks near roads into account
    share_2_buf = (track_2_sum + buffer_2_sum + lane_2_sum) / (primary_sum + secondary_sum),
    share_3_buf = (track_3_sum + buffer_3_sum + lane_3_sum) / (primary_sum + secondary_sum + tertiary_sum)
  )# %>%
# Use only fields that are needed
#select(name, primary.sum, secondary.sum, tertiary.sum, buffer.2.sum, 
#       buffer.3.sum, lane.2.sum, lane.3.sum, track.2.sum, track.3.sum, share.2, share.3, share.2.buf, share.3.buf)

# Note: Double Tagging is possible (e.g. street with tag cycleway=track and seperatly tagged cycleway).
# Thus, a share can become larger than 1
cycle_infrastructure.types$share_2_buf_z<-as.numeric(scale(cycle_infrastructure.types$share_2_buf))
cycle_infrastructure.types$share_3_buf_z<-as.numeric(scale(cycle_infrastructure.types$share_3_buf))
cycle_infrastructure.types[is.na(cycle_infrastructure.types)] <- 0


cycle_infrastructure.final<-cycle_infrastructure.types[order(cycle_infrastructure.types$xid),]


dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_infrastructure", aggr_schema,location) )
psqlPutTable(con, aggr_schema, sprintf("%s_infrastructure", location), cycle_infrastructure.final)
 




############## other
######################


other.query <- sprintf("with facilities AS (select 
							t.id, 
                            %s_facility_node.pos, 
                            t.v, 
                            t.k   
                            from osm.%s_facility_ntag t 
                            LEFT JOIN osm.%s_facility_node on t.id =%s_facility_node.id 
                            where (k='amenity' and v='bicycle_rental') or (k='shop' and v='bicycle'))
                            SELECT b.name,
                            Count(*) count, 
                            cOALESCE(p.v,p.k) as type
                            --INTO osm.%s_bike_facilities_count
                            FROM %s.%s_boundaries b,
                            facilities p
                            WHERE ST_WITHIN(ST_TRANSFORM(p.pos,3857),b.geometry)
                            GROUP By b.name, pos, p.v, p.k",
                                                  location,
                                                  location,
                                                  location, 
                                                  location,
                                                  location, 
                                                  aggr_schema,
												  location)
#print(other.query)
other.intersected  <- set_utf8(dbGetQuery(con, other.query))

print(other.query)

boundaries.query <- sprintf("SELECT DISTINCT name, area from %s.%s_boundaries",aggr_schema, location)
boundaries.name <- set_utf8(dbGetQuery(con, boundaries.query))
# Execute Query and encode to utf-8 to avoid artifacts with umlauts


# Make sure that all districts occur
other.intersected <- boundaries.name %>% left_join(other.intersected)
# Remove NAs in order to avoid errors with aggregate functions
other.intersected[is.na(other.intersected[, "count"]), "count"] <- 0


other.alltypes <- other.intersected %>% group_by(name, area) %>% summarize(n=sum(count))
other.alltypes$density<-other.alltypes$n/other.alltypes$area#

psqlPutTable(con, aggr_schema, sprintf("%s_other", location), other.alltypes)


if("bicycle_rental" %in% colnames(cycle_infrastructure.intersected)){
	other.details <- other.intersected %>% group_by(name, type, area) %>% 
			summarize(count=sum(count)) %>% filter(!is.na(type)) %>% spread(type, count, fill = 0)%>% 
			mutate(
					all_=bicycle+bicycle_rental,
					bicycle_density=bicycle/area,
					bicycle_rental_density=bicycle_rental/area,
					all_density_sum=bicycle_density+bicycle_rental_density)

}else{ other.details <- other.intersected %>% group_by(name, type, area) %>% 
			summarize(count=sum(count)) %>% filter(!is.na(type)) %>% spread(type, count, fill = 0)%>% 
			mutate(
					all_=bicycle,
					bicycle_density=bicycle/area,
					all_density_sum=bicycle_density)
	
}


dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_other", aggr_schema,location) )
psqlPutTable(con, aggr_schema, sprintf("%s_other", location), other.details)


# 
########################
## InfRad
## Gr�nfl�chenauswertung
## Author: Marius Lehne
########################



green.query <- sprintf("SELECT  name, 
                                
                                ST_AREA(way) area FROM %s.%s_parks",aggr_schema, location )
boundary.query <- sprintf("SELECT DISTINCT name, area as area_boundary from %s.%s_boundaries", aggr_schema, location)


# Execute Query and encode to utf-8 to avoid artifacts with umlauts
boundaries.name <- set_utf8(dbGetQuery(con, boundary.query))
green.intersected  <- boundaries.name %>% left_join(set_utf8(dbGetQuery(con, green.query)))%>%
  mutate(
    green_share=((area)/1000)/area_boundary
    #green.share=(area)/area_boundary
  )

green.intersected$green_share_z <- as.numeric(scale(green.intersected$green_share)) 


dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_green", aggr_schema,location) )
psqlPutTable(con, aggr_schema, sprintf("%s_green", location), green.intersected)






connectivity_query <- sprintf("DROP TABLE IF EXISTS %s.%s_intersections_density;
                  
                SELECT name, way, count(n.geom)/ST_AREA(b.geometry)*1000 as dens, count(n.geom) 
                as count, ST_AREA(b.geometry)/1000 as area  
                into %s.%s_intersections_density
                from %s.%s_boundaries b 
                LEFT JOIN osm.%s_network_intersection_clustered n 
                on st_contains(ST_TRANSFORM(b.geometry, 3857), ST_TRANSFORM(n.geom, 3857))
                GROUP BY b.name, b.geometry",aggr_schema, location, aggr_schema, location, aggr_schema, location, location)
print(connectivity_query)
dbGetQuery(con, connectivity_query)
merged <- dbGetQuery(con, sprintf("Select name, count, area, dens from %s.%s_intersections_density",aggr_schema, location))


# #merge connectivity and others
connectivity_other<-merge(x=merged,y=other.details, by="name", all.x=T)


dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_connetivity", aggr_schema,location) )
psqlPutTable(con, "bikeability", "connectivity", connectivity_other)


sql_query <- sprintf("SELECT inf.name jid, 
inf.share_2_buf facilities,
int.dens connectivity,
o.all_density_sum share_repair,
s.small_streets_share street_types,
g.green_share green
from 	%s.%s_infrastructure inf
left join %s.%s_intersections_density int on inf.name = int.name
left join %s.%s_other o on inf.name = o.name
left join %s.%s_street_types s on inf.name = s.name
left join %s.%s_green g on inf.name = g.name
",aggr_schema, location, aggr_schema, location, aggr_schema,location, aggr_schema,location, aggr_schema,location)

bikeability_df <- dbGetQuery(con, sql_query)
bikeability_df[is.na(bikeability_df)] <- 0
bikeability_df$street_types_z <- as.numeric(scale(bikeability_df$street_types))
bikeability_df$connectivity_z <- as.numeric(scale(bikeability_df$connectivity))
bikeability_df$green_z <- as.numeric(scale(bikeability_df$green))
bikeability_df$facilities_z <- as.numeric(scale(bikeability_df$facilities))
bikeability_df$share_repair_z <- as.numeric(scale(bikeability_df$share_repair))
bikeability_df[is.na(bikeability_df)] <- 0

bikeability_df$bikeability <- bikeability_df$street_types_z*0.1651828+
		bikeability_df$connectivity_z*0.2315489+
		bikeability_df$facilities_z*0.2828365+
		bikeability_df$green_z*0.1559295+
		bikeability_df$share_repair_z*0.0817205

dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_bikeability_tmp", aggr_schema,location) )
psqlPutTable(con,aggr_schema, sprintf("%s_bikeability_tmp",location), bikeability_df)
dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_bikeability", aggr_schema,location) )
dbGetQuery(con, sprintf("SELECT int.geometry::GEOMETRY(POLYGON, 3857) geom, b.*
								into %s.%s_bikeability	
 								from 
								%s.%s_bikeability_tmp b
								left join 
								%s.%s_intersections_density int on b.jid=int.name
								",aggr_schema, location, aggr_schema, location, aggr_schema, location))

dbGetQuery(con, sprintf("Drop Table IF EXISTS %s.%s_bikeability_tmp", aggr_schema,location) )								



