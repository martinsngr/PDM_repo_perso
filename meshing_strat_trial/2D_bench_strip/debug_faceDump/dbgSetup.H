// DEBUG ONLY (scratch copy): faces/cells of the 2D bench (50 x 1 x 15 cells,
// slab k = 3..10) printed during the first steps. Not for the solver repo.
labelList dbgF;
wordList dbgN;
labelList dbgC;
wordList dbgCN;
{
    if (mesh.nCells() != 750) FatalErrorInFunction << "debug build: bench mesh only" << exit(FatalError);
    const labelUList& own = mesh.owner();
    const labelUList& nei = mesh.neighbour();
    auto c = [](label i, label k) { return i + 50*k; };
    auto find = [&](label a, label b)
    {
        forAll(nei, f)
        {
            if ((own[f] == a && nei[f] == b) || (own[f] == b && nei[f] == a)) return label(f);
        }
        return label(-1);
    };
    const label fs[][4] = {
        {0, 10, 0, 11}, {1, 10, 1, 11}, {2, 10, 2, 11}, {8, 10, 8, 11},   // top yarn|gap faces
        {0, 9, 0, 10}, {1, 9, 1, 10},                                      // yarn|yarn below the edge row
        {0, 10, 1, 10}, {1, 10, 2, 10}};                                   // x-faces along the edge row
    const char* fn[] = {"YG0", "YG1", "YG2", "YG8", "YY0", "YY1", "X01", "X12"};
    for (label j = 0; j < 8; j++)
    {
        dbgF.append(find(c(fs[j][0], fs[j][1]), c(fs[j][2], fs[j][3])));
        dbgN.append(fn[j]);
    }
    const label cs[][2] = {{0, 9}, {0, 10}, {0, 11}, {1, 10}, {1, 11}, {8, 10}, {8, 11}};
    const char* cn[] = {"c0_9", "c0_10", "c0_11", "c1_10", "c1_11", "c8_10", "c8_11"};
    for (label j = 0; j < 7; j++) { dbgC.append(c(cs[j][0], cs[j][1])); dbgCN.append(cn[j]); }
    Info<< "DBG faces " << dbgF << " owners";
    forAll(dbgF, j) Info<< " " << own[dbgF[j]] << "/" << nei[dbgF[j]];
    Info<< endl;
}
#define DBGON (runTime.timeIndex() <= 2)
#define DBGS(name, fld) if (DBGON) { Info<< "DBGF " << runTime.timeIndex() << " " << name; forAll(dbgF, j_) Info<< " " << dbgN[j_] << "=" << (fld)[dbgF[j_]]; Info<< endl; }
#define DBGC(name, fld) if (DBGON) { Info<< "DBGC " << runTime.timeIndex() << " " << name; forAll(dbgC, j_) Info<< " " << dbgCN[j_] << "=" << (fld)[dbgC[j_]]; Info<< endl; }
