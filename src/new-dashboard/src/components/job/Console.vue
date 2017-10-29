<template>
    <div>
        <md-table-card class="console-table">
            <md-table>
                <md-table-header class="text-right">
                    <md-table-row>
                        <md-table-head class="console-table"><span class="p-xxl">Console Output</span></md-table-head>
                        <md-table-head class="console-table text-right"><span class="text-right">Lines</span></md-table-head>
                        <md-table-head class="console-table text-right"><span class="text-right">Duration</span></md-table-head>
                    </md-table-row>
                </md-table-header>
                <md-table-body>
                    <md-table-row>
                        <md-table-cell class="console-table"><md-card-expand>
                                <md-card-actions class="console-table text-left text-top">
                                    <md-button class="md-icon-button md-raised md-accent" md-expand-trigger>
                                        <md-icon>expand_less</md-icon>
                                    </md-button>
                                    <span class="m-l-md md-body-2" style="flex: 1">Step 1 : FROM alpine:3.6</span>
                                </md-card-actions>
                                <md-card-content class="no-padding">
<pre class="inherit-font no-margin p-l-xxl">10:49:11|3.6: Pulling from library/alpine
10:49:12|88286f41530e: Pulling fs layer
10:49:12|88286f41530e: Verifying Checksum
10:49:12|88286f41530e: Download complete
10:49:12|88286f41530e: Pull complete
10:49:12|Digest: sha256:f006ecbb824d87947d0b51ab8488634bf69fe4094959d935c0c103f4820a417d
10:49:12|Status: Downloaded newer image for alpine:3.6
10:49:12| ---> 76da55c8019d</pre>
                                </md-card-content>
                            </md-card-expand>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">5 lines</div>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">23 sec</div>
                        </md-table-cell>
                    </md-table-row>
                    <md-table-row>
                        <md-table-cell class="console-table"><md-card-expand>
                                <md-card-actions class="console-table text-left text-top">
                                    <md-button class="md-icon-button md-raised md-accent m-r-md" md-expand-trigger>
                                        <md-icon>expand_less</md-icon>
                                    </md-button>
                                  <span class="m-l-md md-body-2" style="flex: 1">Step 2 : RUN apk add --no-cache git python openssh-client</span>
                                </md-card-actions>
                                <md-card-content class="no-padding">
<pre class="inherit-font no-margin p-l-xxl">10:49:12| ---> Running in d647b4ca1211
10:49:12|fetch http://dl-cdn.alpinelinux.org/alpine/v3.6/main/x86_64/APKINDEX.tar.gz
10:49:13|fetch http://dl-cdn.alpinelinux.org/alpine/v3.6/community/x86_64/APKINDEX.tar.gz
10:49:14|(1/17) Installing ca-certificates (20161130-r2)
10:49:14|(2/17) Installing libssh2 (1.8.0-r1)
10:49:14|(3/17) Installing libcurl (7.56.1-r0)
10:49:14|(4/17) Installing expat (2.2.0-r1)
10:49:14|(5/17) Installing pcre (8.41-r0)
10:49:14|(6/17) Installing git (2.13.5-r0)
10:49:14|(7/17) Installing openssh-keygen (7.5_p1-r1)
10:49:14|(8/17) Installing openssh-client (7.5_p1-r1)
10:49:14|(9/17) Installing libbz2 (1.0.6-r5)
10:49:14|(10/17) Installing libffi (3.2.1-r3)
10:49:14|(11/17) Installing gdbm (1.12-r0)
10:49:14|(12/17) Installing ncurses-terminfo-base (6.0_p20170930-r0)
10:49:14|(13/17) Installing ncurses-terminfo (6.0_p20170930-r0)
10:49:15|(14/17) Installing ncurses-libs (6.0_p20170930-r0)
10:49:15|(15/17) Installing readline (6.3.008-r5)
10:49:15|(16/17) Installing sqlite-libs (3.20.1-r0)
10:49:15|(17/17) Installing python2 (2.7.13-r1)
10:49:15|Executing busybox-1.26.2-r5.trigger
10:49:15|Executing ca-certificates-20161130-r2.trigger
10:49:16|OK: 74 MiB in 28 packages
10:49:20| ---> 7b8d902c0b0b
10:49:20|Removing intermediate container d647b4ca1211</pre>
                                </md-card-content>
                            </md-card-expand>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">10 lines</div>
                        </md-table-cell>
                        <md-table-cell class="console-table text-top">
                            <div class="p-t-sm">1023 sec</div>
                        </md-table-cell>
                    </md-table-row>
                </md-table-body>
            </md-table>
        </md-table-card>
    </div>
</template>

<script>
    export default {
        name: 'Console'
    }
</script>

<style scoped>
    .console-table {
        background-color: #273439 !important;
        color: white !important;
        box-shadow: none;
    }
</style>
