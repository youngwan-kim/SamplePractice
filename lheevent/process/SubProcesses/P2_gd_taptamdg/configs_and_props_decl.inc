      INTEGER IFR,LMAXCONFIGS_USED,MAX_BRANCH_USED
      PARAMETER (LMAXCONFIGS_USED=  96)
      PARAMETER (MAX_BRANCH_USED =   5)
      INTEGER MAPCONFIG_D( 14,0:LMAXCONFIGS_USED)
      INTEGER IFOREST_D( 14,2,-MAX_BRANCH_USED:-1,LMAXCONFIGS_USED)
      INTEGER SPROP_D( 14,-MAX_BRANCH_USED:-1,LMAXCONFIGS_USED)
      INTEGER TPRID_D( 14,-MAX_BRANCH_USED:-1,LMAXCONFIGS_USED)
      DOUBLE PRECISION PMASS_D( 14,-MAX_BRANCH_USED:-1
     $ ,LMAXCONFIGS_USED)
      DOUBLE PRECISION PWIDTH_D( 14,-MAX_BRANCH_USED:-1
     $ ,LMAXCONFIGS_USED)
      INTEGER POW_D( 14,-MAX_BRANCH_USED:-1,LMAXCONFIGS_USED)