
:: TODO1 probably don't need this.

cls

echo off

pushd ..\PyBagOfTricks\tests
python -m unittest test_pdb test_tracer
popd

