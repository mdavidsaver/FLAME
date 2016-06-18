
from __future__ import print_function

from math import sqrt

import unittest
import numpy
from numpy import testing as NT
from numpy.testing import assert_array_almost_equal_nulp as assert_aequal

from .. import Machine
import sys

class testMomentSingle(unittest.TestCase):
    def setUp(self):
        self.M = Machine(b'''
sim_type = "MomentMatrix";
Frf = 80.5e6;
IonEs = 930e6;
IonEk = 500e3;
IM = [1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      0,0,0,0,0,0,0
      ];
IV = [1, 1, 0, 0, 0, 0, 0];
TM = [1,0,0,0,0,0,0,
      0,1,0,0,0,0,0,
      0,0,1,0,0,0,0,
      0,0,0,1,0,0,0,
      0,0,0,0,1,0,0,
      0,0,0,0,0,1,0,
      0,0,0,0,0,0,1];
elem0 : source, initial = IM, moment0=IV;
foo : LINE = (elem0);
''')

    def test_config(self):
        C = self.M.conf()
        self.assertTrue("elements" in C)
        self.assertEqual(C['IonEk'], 500e3)
        assert_aequal(C['IV'], numpy.asfarray([1,1,0,0,0,0,0]))

    expect = numpy.asfarray([
        [1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1, -0.001193, 1, 0],
        [1, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 1, -0.001193, 1, 0],
        [1, -0.001193, 1.00000142, -0.001193, 1, -0.001193, 0],
        [0, 1, 0, 1, -0.001193, 1, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ])

    def test_source(self):
        "Initialize w/ all zeros, then propagate through source element to overwrite"
        C = self.M.conf()

        S = self.M.allocState({}, inherit=False)

        self.M.propagate(S, max=1) # propagate through source element

        self.assertEqual(S.pos, 0.0)
        self.assertEqual(S.real_IonEs, C['IonEs'])
        self.assertEqual(S.real_IonW, C['IonEk']+C['IonEs'])
        self.assertEqual(S.real_IonEk, C['IonEk'])
        self.assertEqual(S.real_gamma, (C['IonEk']+C['IonEs'])/C['IonEs'])
        self.assertAlmostEqual(S.real_beta, sqrt(1-1/(S.real_gamma**2)))

        print("moment0",  S.moment0_env, C['IV'])
        assert_aequal(S.moment0_env, C['IV'])
        print("state", S.moment1_env, C['IM'])
        assert_aequal(S.moment1_env, C['IM'].reshape((7,7)), 1e10)

class testMomentMulti(unittest.TestCase):
    lattice = b'''
sim_type = "MomentMatrix";
Frf = 80.5e6;
IonEs = 1.0;
IonEk = 1.0;
IM0 = [1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      0,0,0,0,0,0,0
      ];
IM1 = [2,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      1,0,1,0,1,0,0,
      0,1,0,1,0,1,0,
      0,0,0,0,0,0,0
      ];
IV0 = [1, 1, 0, 0, 0, 0, 0];
IV1 = [2, 2, 0, 0, 0, 0, 0];
TM = [1,0,0,0,0,0,0,
      0,1,0,0,0,0,0,
      0,0,1,0,0,0,0,
      0,0,0,1,0,0,0,
      0,0,0,0,1,0,0,
      0,0,0,0,0,1,0,
      0,0,0,0,0,0,1];
IonChargeStates = [42, 43];
NCharge = [1000, 1010];
elem0 : source, vector_variable="IV", matrix_variable="IM";
foo : LINE = (elem0);
'''

    def test_source_single(self):
        """See that source element initializes correctly for a single charge state

        Use cstate=1 to select
        S.IonZ = IonChargeStates[1]
        S.moment0_env = IV1
        S.moment1_env = IM1
        """
        M = Machine(self.lattice, extra={"cstate":1})
        C = M.conf()

        S = M.allocState({}, inherit=False) # defaults

        M.propagate(S, max=1) # propagate through source element

        self.assertEqual(S.pos, 0.0)
        self.assertEqual(S.ref_IonEk, 1.0)
        self.assertEqual(S.ref_IonEs, 1.0)
        self.assertEqual(S.ref_gamma, 2.0)
        self.assertAlmostEqual(S.ref_beta, 0.8660254037844386)

        assert_aequal(S.IonQ, C['NCharge'][1:])

        print("moment0",  S.moment0_env, C['IV1'])
        assert_aequal(S.moment0_env, C['IV1'])
        print("state", S.moment1_env, C['IM1'])
        assert_aequal(S.moment1_env, C['IM1'].reshape((7,7)), 1e10)

    def test_source_multi(self):
        """See that source element initializes correctly for many (two) charge states

        Use cstate=1 to select
        S.IonZ = IonChargeStates[1]
        S.moment0_env = IV1
        S.moment1_env = IM1
        """
        M = Machine(self.lattice)
        C = M.conf()

        S = M.allocState({}, inherit=False) # defaults

        M.propagate(S, max=1) # propagate through source element

        self.assertEqual(S.pos, 0.0)
        self.assertEqual(S.ref_IonEk, 1.0)
        self.assertEqual(S.ref_IonEs, 1.0)
        self.assertEqual(S.ref_gamma, 2.0)
        self.assertAlmostEqual(S.ref_beta, 0.8660254037844386)

        assert_aequal(S.IonQ, C['NCharge'])

        IV  = C['IV0']*S.IonQ[0]
        IV += C['IV1']*S.IonQ[1]
        IV /= S.IonQ.sum()

        #IM0 = C['IM0'].reshape((7,7))
        #IM1 = C['IM1'].reshape((7,7))
        #IM  = numpy.zeros(IM0.shape)
        #for Q in S.IonQ:
        #    IM[:7,:7] +=

        print("moment0",  S.moment0_env, IV)
        assert_aequal(S.moment0_env, IV)
        #print("state", S.moment1_env, IM)
        #assert_aequal(S.moment1_env, IM, 1e10)
