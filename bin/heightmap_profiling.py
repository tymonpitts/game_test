import game_core
heightmap = game_core.HeightMap(size=512.0, max_height=256.0, max_depth=9, seed=1121327837)
corner = game_core.Point(heightmap.size / 2.0, heightmap.size / 2.0)
area = game_core.BoundingBox2D(-corner, corner)
heightmap.generate_area(area)
print 'DONE'
