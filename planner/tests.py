from django.test import SimpleTestCase
from .optimizer import Stop, optimize, Infeasible
class OptimizerTests(SimpleTestCase):
    def test_short_trip(self):
        purchases,left=optimize([],100,50,0)
        self.assertEqual(purchases,[])
        self.assertAlmostEqual(left,40)
    def test_cheaper_ahead(self):
        purchases,left=optimize([Stop(100,4,"A"),Stop(400,2,"B")],900,50,0)
        self.assertEqual([p["station"] for p in purchases],["B"])
        self.assertAlmostEqual(purchases[0]["gallons"],40)
        self.assertAlmostEqual(purchases[0]["cost"],80)
        self.assertAlmostEqual(left,0)
    def test_multiple_stops(self):
        purchases,left=optimize([Stop(400,3,"A"),Stop(800,4,"B")],1200,50,0)
        self.assertAlmostEqual(sum(p["gallons"] for p in purchases),70)
        self.assertAlmostEqual(sum(p["cost"] for p in purchases),240)
    def test_unreachable(self):
        with self.assertRaises(Infeasible): optimize([],501,50,0)
    def test_initial_fuel(self):
        with self.assertRaises(Infeasible): optimize([Stop(200,3)],300,10,0)
    def test_reserve(self):
        purchases,left=optimize([Stop(450,3)],900,50,2)
        self.assertAlmostEqual(left,2)
        self.assertAlmostEqual(sum(p["gallons"] for p in purchases),42)
