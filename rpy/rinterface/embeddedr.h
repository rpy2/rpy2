#ifndef _RPY_PRIVATE_EMBEDDEDR_H_
#define _RPY_PRIVATE_EMBEDDEDR_H_

extern const unsigned int const RPY_R_INITIALIZED;
extern const unsigned int const RPY_R_BUSY;
static void embeddedR_setlock(void);
static void embeddedR_freelock(void);
static unsigned int rpy_has_status(unsigned int);
static unsigned int embeddedR_status;
#endif


