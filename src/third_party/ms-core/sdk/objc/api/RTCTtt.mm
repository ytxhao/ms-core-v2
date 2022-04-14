//
//  ttt.m
//  test007
//
//  Created by yuhao on 2022/4/13.
//

#import "RTCTtt.h"

@implementation RTCTtt

@synthesize connected = _connected;
-(void)t {
     NSLog(@"123!");
}

- (instancetype)init {
    self = [super init];
    if (self) {
        self.connected = YES;
    }
    NSLog(@"RTCTtt init");
    return self;
}

- (void)dealloc {
    NSLog(@"RTCTtt dealloc");
}
@end
