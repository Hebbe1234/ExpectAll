graph [
  directed 1
  multigraph 1
  DateObtained "22/10/10"
  GeoLocation "Tokyo, Japan"
  GeoExtent "Metro"
  Network "T-lex"
  Provenance "Primary"
  Access 0
  Source "http://www.t-lex.net/"
  Version "1.0"
  DateType "Current"
  Type "REN"
  Backbone 1
  Commercial 0
  label "TLex"
  ToolsetVersion "0.3.34dev-20120328"
  Customer 0
  IX 1
  SourceGitVersion "e278b1b"
  DateModifier "="
  DateMonth "08"
  LastAccess "3/08/10"
  Layer "Layer 2"
  Creator "Topology Zoo Toolset"
  Developed 1
  Transit 1
  NetworkDate "2010_08"
  DateYear "2010"
  LastProcessed "2011_09_01"
  Testbed 0
  node [
    id 0
    label "0"
    Internal 0
  ]
  node [
    id 1
    label "1"
    Internal 0
  ]
  node [
    id 2
    label "2"
    Internal 1
  ]
  node [
    id 3
    label "3"
    Country "France"
    Longitude 1.92302
    Internal 1
    Latitude 49.41631
  ]
  node [
    id 4
    label "4"
    Internal 0
  ]
  node [
    id 5
    label "5"
    Internal 0
  ]
  node [
    id 6
    label "6"
    Internal 0
  ]
  node [
    id 7
    label "7"
    Internal 0
  ]
  node [
    id 8
    label "8"
    Internal 0
  ]
  node [
    id 9
    label "9"
    Internal 0
  ]
  node [
    id 10
    label "10"
    Internal 1
  ]
  node [
    id 11
    label "11"
    Internal 1
  ]
  edge [
    source 0
    target 3
    key 0
    LinkType "OC-12"
    LinkLabel "OC-12"
    distance 0.4519287683282547
  ]
  edge [
    source 0
    target 3
    key 1
    LinkType "OC-192"
    LinkLabel "OC-192"
    distance 0.4519287683282547
  ]
  edge [
    source 1
    target 3
    key 0
    LinkType "OC-192"
    LinkLabel "OC-192 (Future)"
    LinkStatus "Future"
    distance 0.9605356057369412
  ]
  edge [
    source 2
    target 11
    key 0
    LinkSpeed "10"
    LinkNote "E"
    LinkLabel "10GE"
    LinkSpeedUnits "G"
    LinkSpeedRaw 10000000000.0
    distance 0.7549616881384451
  ]
  edge [
    source 2
    target 3
    key 0
    LinkLabel "WANPHY"
    distance 0.3182446616170185
  ]
  edge [
    source 2
    target 3
    key 1
    LinkType "OC-48"
    LinkLabel "OC-48"
    distance 0.3182446616170185
  ]
  edge [
    source 3
    target 0
    key 0
    LinkType "OC-12"
    LinkLabel "OC-12"
    distance 0.9303244364514685
  ]
  edge [
    source 3
    target 0
    key 1
    LinkType "OC-192"
    LinkLabel "OC-192"
    distance 0.9303244364514685
  ]
  edge [
    source 3
    target 1
    key 0
    LinkType "OC-192"
    LinkLabel "OC-192 (Future)"
    LinkStatus "Future"
    distance 0.7729737051378727
  ]
  edge [
    source 3
    target 2
    key 0
    LinkLabel "WANPHY"
    distance 0.3049832098286099
  ]
  edge [
    source 3
    target 2
    key 1
    LinkType "OC-48"
    LinkLabel "OC-48"
    distance 0.3049832098286099
  ]
  edge [
    source 3
    target 11
    key 0
    LinkLabel "WANPHY"
    distance 0.8234088058567812
  ]
  edge [
    source 3
    target 10
    key 0
    LinkLabel "8*GbE"
    distance 0.34137238557178695
  ]
  edge [
    source 3
    target 10
    key 1
    id "e6"
    distance 0.34137238557178695
  ]
  edge [
    source 4
    target 11
    key 0
    id "e0"
    distance 0.3015153661516957
  ]
  edge [
    source 5
    target 11
    key 0
    id "e1"
    distance 0.5705119339200992
  ]
  edge [
    source 6
    target 11
    key 0
    id "e2"
    distance 1.0266843867513618
  ]
  edge [
    source 7
    target 11
    key 0
    id "e3"
    distance 0.9692060809413205
  ]
  edge [
    source 8
    target 11
    key 0
    id "e4"
    distance 0.8092878663537869
  ]
  edge [
    source 9
    target 10
    key 0
    id "e5"
    distance 1.219566822627747
  ]
  edge [
    source 10
    target 3
    key 0
    LinkLabel "8*GbE"
    distance 0.7642003663532915
  ]
  edge [
    source 10
    target 3
    key 1
    id "e6"
    distance 0.7642003663532915
  ]
  edge [
    source 10
    target 9
    key 0
    id "e5"
    distance 1.4436438481117968
  ]
  edge [
    source 10
    target 11
    key 0
    id "e8"
    distance 0.671442692088358
  ]
  edge [
    source 11
    target 2
    key 0
    LinkSpeed "10"
    LinkNote "E"
    LinkLabel "10GE"
    LinkSpeedUnits "G"
    LinkSpeedRaw 10000000000.0
    distance 0.4907026972103899
  ]
  edge [
    source 11
    target 3
    key 0
    LinkLabel "WANPHY"
    distance 0.8390008496854684
  ]
  edge [
    source 11
    target 4
    key 0
    id "e0"
    distance 0.6123789051332877
  ]
  edge [
    source 11
    target 5
    key 0
    id "e1"
    distance 1.101382152196334
  ]
  edge [
    source 11
    target 6
    key 0
    id "e2"
    distance 0.4014568664977613
  ]
  edge [
    source 11
    target 7
    key 0
    id "e3"
    distance 0.9345754978465963
  ]
  edge [
    source 11
    target 8
    key 0
    id "e4"
    distance 1.2196053092742316
  ]
  edge [
    source 11
    target 10
    key 0
    id "e8"
    distance 0.7339690809935567
  ]
]
