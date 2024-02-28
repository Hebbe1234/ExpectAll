graph [
  directed 1
  multigraph 1
  DateObtained "22/10/10"
  GeoLocation "Beijing, China"
  GeoExtent "Metro"
  Network "NSFCNET"
  Provenance "Primary"
  Note "Hard to tell if multiple POS OC-48 links"
  Source "http://www.cn.apan.net/nsfcmap.htm"
  Version "1.0"
  Type "REN"
  DateType "Current"
  Backbone 1
  Commercial 0
  label "Nsfcnet"
  ToolsetVersion "0.3.34dev-20120328"
  Customer 0
  IX 0
  SourceGitVersion "e278b1b"
  DateModifier "="
  DateMonth "10"
  LastAccess "7/10/10"
  Access 0
  Layer "IP"
  Creator "Topology Zoo Toolset"
  Developed 0
  Transit 0
  NetworkDate "2010_10"
  DateYear "2010"
  LastProcessed "2011_09_01"
  Testbed 1
  node [
    id 0
    label "0"
    Internal 1
    type "Router"
  ]
  node [
    id 1
    label "1"
    Internal 0
  ]
  node [
    id 2
    label "2"
    Internal 0
  ]
  node [
    id 3
    label "3"
    Internal 0
  ]
  node [
    id 4
    label "4"
    Internal 1
    type "Router"
  ]
  node [
    id 5
    label "5"
    Internal 1
    type "Router"
  ]
  node [
    id 6
    label "6"
    Internal 1
    type "Router"
  ]
  node [
    id 7
    label "7"
    Internal 1
    type "Router"
  ]
  node [
    id 8
    label "8"
    Internal 1
    type "Router"
  ]
  node [
    id 9
    label "9"
    Internal 0
  ]
  edge [
    source 0
    target 8
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.03669521107222753
  ]
  edge [
    source 0
    target 4
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.25645353347992134
  ]
  edge [
    source 2
    target 4
    key 0
    id "e0"
    distance 0.11841762742471831
  ]
  edge [
    source 3
    target 4
    key 0
    LinkLabel "GE"
    distance 0.31584824281581486
  ]
  edge [
    source 4
    target 0
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.1682855257976346
  ]
  edge [
    source 4
    target 2
    key 0
    id "e0"
    distance 0.11827369220125791
  ]
  edge [
    source 4
    target 3
    key 0
    LinkLabel "GE"
    distance 0.2748332327617842
  ]
  edge [
    source 4
    target 5
    key 0
    LinkLabel "DPT ring"
    distance 0.40053240264701273
  ]
  edge [
    source 4
    target 7
    key 0
    LinkLabel "DPT Ring"
    distance 0.2941694636631315
  ]
  edge [
    source 4
    target 8
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.16111635093223645
  ]
  edge [
    source 5
    target 4
    key 0
    LinkLabel "DPT ring"
    distance 0.21805041231059075
  ]
  edge [
    source 5
    target 6
    key 0
    LinkLabel "DPT Ring"
    distance 0.36504400633317685
  ]
  edge [
    source 6
    target 5
    key 0
    LinkLabel "DPT Ring"
    distance 0.15800284549646776
  ]
  edge [
    source 6
    target 7
    key 0
    LinkLabel "DPT Ring"
    distance 0.16831706975269228
  ]
  edge [
    source 7
    target 4
    key 0
    LinkLabel "DPT Ring"
    distance 0.1336635217389012
  ]
  edge [
    source 7
    target 6
    key 0
    LinkLabel "DPT Ring"
    distance 0.2936635075677839
  ]
  edge [
    source 8
    target 0
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.15404037563617207
  ]
  edge [
    source 8
    target 4
    key 0
    LinkType "OC-48"
    LinkLabel "POS OC-48"
    LinkNote "POS "
    distance 0.35727607611303547
  ]
  edge [
    source 8
    target 9
    key 0
    LinkLabel "GE"
    distance 0.12203161926873442
  ]
  edge [
    source 9
    target 8
    key 0
    LinkLabel "GE"
    distance 0.33830620828111096
  ]
]
