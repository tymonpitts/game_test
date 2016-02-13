from tempest import core
heightmap = core.HeightMap(size=512, max_height=256.0, max_depth=9, seed=1121327837)
corner = core.Point(heightmap.size()/2, heightmap.size()/2)
area = core.BoundingBox2D(-corner, corner)
heightmap.generate_area(area)
print 'DONE'