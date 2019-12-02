import rdflib
import json
from geomet import wkt
import os

dir_path = os.path.dirname(os.path.realpath(__file__)) + "\\"

def getGeoConceptsFromGraph(graph):
    viewlist=[]
    qres = graph.query(
    """SELECT DISTINCT ?a_class (count( ?a_class) as ?count)
    WHERE {
          ?a rdf:type ?a_class .
          ?a geo:hasGeometry ?a_geom .
          ?a_geom geo:asWKT ?a_wkt .
       }""")
    print(qres)
    for row in qres:
        viewlist.append(str(row[0]))
    return viewlist

def getGeoJSONFromGeoConcept(graph,concept):
    qres = graph.query(
    """SELECT DISTINCT ?a ?rel ?val ?wkt
    WHERE {
          ?a rdf:type <"""+concept+"""> .
          ?a ?rel ?val .
          OPTIONAL { ?val geo:asWKT ?wkt}
       }""")
    geos=[]
    geometries = {
    'type': 'FeatureCollection',
    'features': geos,
    }
    newfeature=False
    lastfeature=""
    currentgeo={}
    for row in qres:
        print(lastfeature+" - "+row[0]+" - "+str(len(row)))
        print(row)
        if(lastfeature=="" or lastfeature!=row[0]):
            if(lastfeature!=""):
                geos.append(currentgeo)
            lastfeature=row[0]
            currentgeo={'id':row[0],'geometry':{},'properties':{}}
        if(row[3]!=None):
            print(row[3])
            if("<" in row[3]):
                currentgeo['geometry']=wkt.loads(row[3].split(">")[1].strip())
            else:
                currentgeo['geometry']=wkt.loads(row[3])
        else:
            currentgeo['properties'][str(row[1])]=str(row[2])
    return geometries

def geoJSONToRDF(geojson):
    ttlstring=""
    for feature in geojson['features']:
        print(feature)
        for prop in feature['properties']:
            ttlstring+="<"+feature['id']+"> <"+prop+"> <"+feature['properties'][prop]+"> .\n"
        ttlstring+="<"+feature['id']+"> <http://www.opengis.net/ont/geosparql#hasGeometry> <"+feature['id']+"_geom> .\n"
        ttlstring+="<"+feature['id']+"_geom> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.opengis.net/ont/geosparql#Geometry> .\n"
        ttlstring+="<"+feature['id']+"_geom> <http://www.opengis.net/ont/geosparql#asWKT> \""+wkt.dumps(feature['geometry'])+"\"^^<http://www.opengis.net/ont/geosparql#wktLiteral> .\n"
    return ttlstring

g = rdflib.Graph()
result = g.parse(dir_path + "archaeological_sites.ttl", format="ttl")

print("graph has %s statements." % len(g))
# prints graph has 79 statements.

row=getGeoConceptsFromGraph(g)
with open(dir_path + "views.txt", "w") as text_file:
    text_file.write(str(row))
geojson=getGeoJSONFromGeoConcept(g,row[0])
with open(dir_path + "Output.geojson", "w") as text_file:
    text_file.write(json.dumps(geojson,indent=2))
with open(dir_path + "Output.ttl", "w") as text_file:
    text_file.write(geoJSONToRDF(geojson))
