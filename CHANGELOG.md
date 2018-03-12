# Change Log

## [Unreleased](https://github.com/infrabox/infrabox/tree/HEAD)

[Full Changelog](https://github.com/infrabox/infrabox/compare/v0.9.7...HEAD)

**Fixed bugs:**

- Job end message should not contain full strack trace for an exception [\#254](https://github.com/InfraBox/infrabox/issues/254)
- job creates branch which already exists [\#252](https://github.com/InfraBox/infrabox/issues/252)
- fails to push to docker hub [\#251](https://github.com/InfraBox/infrabox/issues/251)
- Incorrect output of API tests [\#238](https://github.com/InfraBox/infrabox/issues/238)
- Dates sometimes show 'Invalid Date' in dashboard [\#234](https://github.com/InfraBox/infrabox/issues/234)
- don't allow access to secrets in PR [\#223](https://github.com/InfraBox/infrabox/issues/223)
- job/build state don't update properly [\#222](https://github.com/InfraBox/infrabox/issues/222)
- fix github connect [\#217](https://github.com/InfraBox/infrabox/issues/217)

**Closed issues:**

- create ib.py scripts [\#257](https://github.com/InfraBox/infrabox/issues/257)
- add entrypoint option [\#247](https://github.com/InfraBox/infrabox/issues/247)
- update generator to not push to latest if it's a alpha/beta/rc [\#243](https://github.com/InfraBox/infrabox/issues/243)
- remove stats container [\#233](https://github.com/InfraBox/infrabox/issues/233)
- add support for no-cache option [\#230](https://github.com/InfraBox/infrabox/issues/230)
- create deployment manager template [\#224](https://github.com/InfraBox/infrabox/issues/224)
- move github-api into api [\#220](https://github.com/InfraBox/infrabox/issues/220)
- badge per branch [\#111](https://github.com/InfraBox/infrabox/issues/111)

**Merged pull requests:**

- Ib py [\#258](https://github.com/InfraBox/infrabox/pull/258) ([ib-steffen](https://github.com/ib-steffen))
- Fixes [\#255](https://github.com/InfraBox/infrabox/pull/255) ([ib-steffen](https://github.com/ib-steffen))
- Fixes [\#241](https://github.com/InfraBox/infrabox/pull/241) ([ib-steffen](https://github.com/ib-steffen))
- Testing [\#239](https://github.com/InfraBox/infrabox/pull/239) ([ib-steffen](https://github.com/ib-steffen))
- Fixes [\#232](https://github.com/InfraBox/infrabox/pull/232) ([ib-steffen](https://github.com/ib-steffen))

## [v0.9.7](https://github.com/infrabox/infrabox/tree/v0.9.7) (2018-02-25)
[Full Changelog](https://github.com/infrabox/infrabox/compare/v0.9.6...v0.9.7)

**Implemented enhancements:**

- change github repos from cards to table [\#206](https://github.com/InfraBox/infrabox/issues/206)
- use mono space font for log [\#186](https://github.com/InfraBox/infrabox/issues/186)
- show job end message in UI [\#185](https://github.com/InfraBox/infrabox/issues/185)
- harmoniz cpu/memory and resources columns [\#182](https://github.com/InfraBox/infrabox/issues/182)
- Improve color legend for Stats [\#175](https://github.com/InfraBox/infrabox/issues/175)
- rewrite tests for job api [\#138](https://github.com/InfraBox/infrabox/issues/138)

**Fixed bugs:**

- correct collor in gantt chart [\#225](https://github.com/InfraBox/infrabox/issues/225)
- dashboard shows commits as PR [\#221](https://github.com/InfraBox/infrabox/issues/221)
- job detail page sometimes shows scrollbar until data is loaded [\#205](https://github.com/InfraBox/infrabox/issues/205)
- Axis labels and graph colors are mismatched on the build stats screen [\#202](https://github.com/InfraBox/infrabox/issues/202)
- remove shallow\_clone option again [\#189](https://github.com/InfraBox/infrabox/issues/189)
- use gosu / su [\#143](https://github.com/InfraBox/infrabox/issues/143)
- dashboard load all running builds [\#141](https://github.com/InfraBox/infrabox/issues/141)
- don't allow tokens with empty names [\#135](https://github.com/InfraBox/infrabox/issues/135)

**Closed issues:**

- Infrabox CLI does not correctly support `build\_context` on Windows [\#214](https://github.com/InfraBox/infrabox/issues/214)
- proposed badges in infrabox UI are broken [\#211](https://github.com/InfraBox/infrabox/issues/211)
- detect OOM and show message [\#210](https://github.com/InfraBox/infrabox/issues/210)
- cannot run child container locally due to missing files [\#209](https://github.com/InfraBox/infrabox/issues/209)
- rename api-new to api [\#200](https://github.com/InfraBox/infrabox/issues/200)
- Parsing junit-reports.xml does not work [\#198](https://github.com/InfraBox/infrabox/issues/198)
- loading testresults takes long time [\#197](https://github.com/InfraBox/infrabox/issues/197)
- Force pushing a rebased branch triggers a build for all commits [\#196](https://github.com/InfraBox/infrabox/issues/196)
- specify a dockerfile in a git job [\#193](https://github.com/InfraBox/infrabox/issues/193)
- docker-compose job does not pick-up coverage reports [\#191](https://github.com/InfraBox/infrabox/issues/191)
- use external docker registries instead of hosting one [\#178](https://github.com/InfraBox/infrabox/issues/178)
- allow configuration of clone depth [\#172](https://github.com/InfraBox/infrabox/issues/172)
- escape env var in "Run Local" [\#168](https://github.com/InfraBox/infrabox/issues/168)
- escape env var in "Run Local [\#167](https://github.com/InfraBox/infrabox/issues/167)
- escape env var in  [\#166](https://github.com/InfraBox/infrabox/issues/166)
- Redirect to build page after trigger [\#164](https://github.com/InfraBox/infrabox/issues/164)
- Make it more obvious that either branch or sha are mandatory in Trigger now [\#163](https://github.com/InfraBox/infrabox/issues/163)
- add examples [\#145](https://github.com/InfraBox/infrabox/issues/145)
- add docker-compose e2e tests [\#144](https://github.com/InfraBox/infrabox/issues/144)
- Add -f option to infrabox run to specify infrabox.json file [\#101](https://github.com/InfraBox/infrabox/issues/101)
- Integrate Google Material icons enhancement [\#96](https://github.com/InfraBox/infrabox/issues/96)
- merge github APIs [\#92](https://github.com/InfraBox/infrabox/issues/92)
- db migration might wait forever [\#59](https://github.com/InfraBox/infrabox/issues/59)

**Merged pull requests:**

-  Fixes \#225 Correct color in Gannt chart [\#228](https://github.com/InfraBox/infrabox/pull/228) ([ib-franziska](https://github.com/ib-franziska))
- fixes [\#227](https://github.com/InfraBox/infrabox/pull/227) ([ib-steffen](https://github.com/ib-steffen))
- Dev doc [\#219](https://github.com/InfraBox/infrabox/pull/219) ([ib-steffen](https://github.com/ib-steffen))
- Style for job error message [\#218](https://github.com/InfraBox/infrabox/pull/218) ([ib-franziska](https://github.com/ib-franziska))
- Detect oom [\#215](https://github.com/InfraBox/infrabox/pull/215) ([ib-steffen](https://github.com/ib-steffen))
- Rewrite dashboard [\#212](https://github.com/InfraBox/infrabox/pull/212) ([ib-steffen](https://github.com/ib-steffen))
- UI fixes [\#208](https://github.com/InfraBox/infrabox/pull/208) ([ib-franziska](https://github.com/ib-franziska))
- Show GitHub repos as table; Changed color of axes, fixes \#202 [\#204](https://github.com/InfraBox/infrabox/pull/204) ([ib-franziska](https://github.com/ib-franziska))
- Fix typo [\#203](https://github.com/InfraBox/infrabox/pull/203) ([vaghetti](https://github.com/vaghetti))
- Change UI look and feel [\#201](https://github.com/InfraBox/infrabox/pull/201) ([ib-franziska](https://github.com/ib-franziska))
- Build context [\#199](https://github.com/InfraBox/infrabox/pull/199) ([ib-steffen](https://github.com/ib-steffen))
- Fixes [\#195](https://github.com/InfraBox/infrabox/pull/195) ([ib-steffen](https://github.com/ib-steffen))
- change api URLs [\#194](https://github.com/InfraBox/infrabox/pull/194) ([ib-steffen](https://github.com/ib-steffen))
- K8s e2e [\#192](https://github.com/InfraBox/infrabox/pull/192) ([ib-steffen](https://github.com/ib-steffen))
- Add Base-Repo URL to GitHub Pull Request env [\#190](https://github.com/InfraBox/infrabox/pull/190) ([Steffen911](https://github.com/Steffen911))
- Try to fix InfraBox logo in sidenav [\#188](https://github.com/InfraBox/infrabox/pull/188) ([ib-franziska](https://github.com/ib-franziska))
- Moncospaced type for console. Fixes \#186 [\#187](https://github.com/InfraBox/infrabox/pull/187) ([ib-franziska](https://github.com/ib-franziska))
- Clone in container [\#184](https://github.com/InfraBox/infrabox/pull/184) ([ib-steffen](https://github.com/ib-steffen))
- Created content when no projects are connected to InfraBox. [\#181](https://github.com/InfraBox/infrabox/pull/181) ([ib-franziska](https://github.com/ib-franziska))
- Stats Chart: Colors of axes matches graph now. [\#180](https://github.com/InfraBox/infrabox/pull/180) ([ib-franziska](https://github.com/ib-franziska))
- New api [\#177](https://github.com/InfraBox/infrabox/pull/177) ([ib-steffen](https://github.com/ib-steffen))
- Auto detect [\#174](https://github.com/InfraBox/infrabox/pull/174) ([ib-steffen](https://github.com/ib-steffen))
- Auto detect coverage [\#173](https://github.com/InfraBox/infrabox/pull/173) ([ib-steffen](https://github.com/ib-steffen))
- Typo [\#171](https://github.com/InfraBox/infrabox/pull/171) ([Steffen911](https://github.com/Steffen911))
- several fixes [\#170](https://github.com/InfraBox/infrabox/pull/170) ([ib-steffen](https://github.com/ib-steffen))
- trigger github build only on opened, reopened, synchronized [\#169](https://github.com/InfraBox/infrabox/pull/169) ([Steffen911](https://github.com/Steffen911))

## [v0.9.6](https://github.com/infrabox/infrabox/tree/v0.9.6) (2017-12-10)
[Full Changelog](https://github.com/infrabox/infrabox/compare/v0.9.5...v0.9.6)

## [v0.9.5](https://github.com/infrabox/infrabox/tree/v0.9.5) (2017-12-10)
[Full Changelog](https://github.com/infrabox/infrabox/compare/v0.9.1...v0.9.5)

**Implemented enhancements:**

- remove base image [\#140](https://github.com/InfraBox/infrabox/issues/140)
- Show message when websocket disconnected [\#137](https://github.com/InfraBox/infrabox/issues/137)

**Fixed bugs:**

- show fav icon for dashboard [\#142](https://github.com/InfraBox/infrabox/issues/142)
- show stats page on job detail page [\#130](https://github.com/InfraBox/infrabox/issues/130)
- show custom output tabs again on job detail page [\#129](https://github.com/InfraBox/infrabox/issues/129)
- Show downloads tab again in job detail page [\#128](https://github.com/InfraBox/infrabox/issues/128)
- jobs always show 'still running' [\#127](https://github.com/InfraBox/infrabox/issues/127)

**Closed issues:**

- Make workflow configuration samples self contained [\#153](https://github.com/InfraBox/infrabox/issues/153)
- Add build now functionality to dashboard [\#150](https://github.com/InfraBox/infrabox/issues/150)
- rework cli tokens [\#148](https://github.com/InfraBox/infrabox/issues/148)
- don't require project ID anymore for cli api [\#146](https://github.com/InfraBox/infrabox/issues/146)
- cache base images for docker-compose jobs [\#136](https://github.com/InfraBox/infrabox/issues/136)
- remove /infrabox directory [\#124](https://github.com/InfraBox/infrabox/issues/124)
- check leader election  [\#123](https://github.com/InfraBox/infrabox/issues/123)
- check file handling in job api [\#121](https://github.com/InfraBox/infrabox/issues/121)
- build status badge not shown in project settings [\#120](https://github.com/InfraBox/infrabox/issues/120)
- set higher timeouts for nginx [\#117](https://github.com/InfraBox/infrabox/issues/117)
- write gcloud install guide [\#114](https://github.com/InfraBox/infrabox/issues/114)
- remove legacy URL configurations [\#108](https://github.com/InfraBox/infrabox/issues/108)
- job should use token to login to docker registry [\#107](https://github.com/InfraBox/infrabox/issues/107)
- Support docker-compose setup again [\#104](https://github.com/InfraBox/infrabox/issues/104)
- Add stats chart [\#103](https://github.com/InfraBox/infrabox/issues/103)
- orphaned jobs [\#60](https://github.com/InfraBox/infrabox/issues/60)

**Merged pull requests:**

- Fixed "success" color [\#161](https://github.com/InfraBox/infrabox/pull/161) ([ib-franziska](https://github.com/ib-franziska))
- Cache compose [\#160](https://github.com/InfraBox/infrabox/pull/160) ([ib-steffen](https://github.com/ib-steffen))
- Test Detail page and several UI fixes [\#159](https://github.com/InfraBox/infrabox/pull/159) ([ib-franziska](https://github.com/ib-franziska))
- New api [\#158](https://github.com/InfraBox/infrabox/pull/158) ([ib-steffen](https://github.com/ib-steffen))
- Fix issues with docker compose setup [\#156](https://github.com/InfraBox/infrabox/pull/156) ([ib-steffen](https://github.com/ib-steffen))
- Typo [\#155](https://github.com/InfraBox/infrabox/pull/155) ([Steffen911](https://github.com/Steffen911))
- Make sample job configurations self-contained \#153 [\#154](https://github.com/InfraBox/infrabox/pull/154) ([Steffen911](https://github.com/Steffen911))
- Fix \#148 & \#146 [\#152](https://github.com/InfraBox/infrabox/pull/152) ([ib-steffen](https://github.com/ib-steffen))
- Update connect\_github.md [\#149](https://github.com/InfraBox/infrabox/pull/149) ([ib-franziska](https://github.com/ib-franziska))
- use has of priv key for dashboard secret [\#147](https://github.com/InfraBox/infrabox/pull/147) ([ib-steffen](https://github.com/ib-steffen))
- Several UI fixes [\#139](https://github.com/InfraBox/infrabox/pull/139) ([ib-franziska](https://github.com/ib-franziska))
- Update README.md [\#134](https://github.com/InfraBox/infrabox/pull/134) ([ib-steffen](https://github.com/ib-steffen))
- fixes [\#133](https://github.com/InfraBox/infrabox/pull/133) ([ib-steffen](https://github.com/ib-steffen))
- update nodejs versions to 8.9 [\#132](https://github.com/InfraBox/infrabox/pull/132) ([ib-steffen](https://github.com/ib-steffen))
- Typo [\#131](https://github.com/InfraBox/infrabox/pull/131) ([Steffen911](https://github.com/Steffen911))

## [v0.9.1](https://github.com/infrabox/infrabox/tree/v0.9.1) (2017-11-19)
[Full Changelog](https://github.com/infrabox/infrabox/compare/v0.9.0...v0.9.1)

**Closed issues:**

- add landing page [\#112](https://github.com/InfraBox/infrabox/issues/112)

**Merged pull requests:**

- Update for readme and landing [\#126](https://github.com/InfraBox/infrabox/pull/126) ([ib-franziska](https://github.com/ib-franziska))
- Add landing content [\#122](https://github.com/InfraBox/infrabox/pull/122) ([ib-franziska](https://github.com/ib-franziska))

## [v0.9.0](https://github.com/infrabox/infrabox/tree/v0.9.0) (2017-11-19)
**Implemented enhancements:**

- reduce   permissions for infrabox-leader-elector [\#49](https://github.com/InfraBox/infrabox/issues/49)
- unify python logging format [\#33](https://github.com/InfraBox/infrabox/issues/33)
- encrypt env vars [\#16](https://github.com/InfraBox/infrabox/issues/16)
- row level security [\#15](https://github.com/InfraBox/infrabox/issues/15)
- rework add project [\#10](https://github.com/InfraBox/infrabox/issues/10)
- rework project list [\#9](https://github.com/InfraBox/infrabox/issues/9)
- do git clone in separate container [\#4](https://github.com/InfraBox/infrabox/issues/4)
- use alpine base images [\#3](https://github.com/InfraBox/infrabox/issues/3)
- remove authHttp [\#2](https://github.com/InfraBox/infrabox/issues/2)

**Fixed bugs:**

- job history shows only one job [\#50](https://github.com/InfraBox/infrabox/issues/50)
- delete project returns 404 [\#17](https://github.com/InfraBox/infrabox/issues/17)
- set no-cache for badges [\#13](https://github.com/InfraBox/infrabox/issues/13)

**Closed issues:**

- merge docs and dashboard-client [\#113](https://github.com/InfraBox/infrabox/issues/113)
- remove old tls configuration [\#109](https://github.com/InfraBox/infrabox/issues/109)
- setup git tag workflow [\#106](https://github.com/InfraBox/infrabox/issues/106)
- Add register page [\#102](https://github.com/InfraBox/infrabox/issues/102)
- remove tls support in API [\#95](https://github.com/InfraBox/infrabox/issues/95)
- job names must be unique [\#93](https://github.com/InfraBox/infrabox/issues/93)
- Job type cannot be restarted [\#82](https://github.com/InfraBox/infrabox/issues/82)
- job-api should be a global api [\#78](https://github.com/InfraBox/infrabox/issues/78)
- make infrabox-system namespace configurable [\#77](https://github.com/InfraBox/infrabox/issues/77)
- reimplement leader election [\#76](https://github.com/InfraBox/infrabox/issues/76)
- remove clone in container [\#75](https://github.com/InfraBox/infrabox/issues/75)
- remove clair [\#74](https://github.com/InfraBox/infrabox/issues/74)
- automountServiceAccountToken: false [\#73](https://github.com/InfraBox/infrabox/issues/73)
- badges should be accessible by branch [\#68](https://github.com/InfraBox/infrabox/issues/68)
- Support docker capabilities [\#64](https://github.com/InfraBox/infrabox/issues/64)
- Support full dynamic workflows [\#62](https://github.com/InfraBox/infrabox/issues/62)
- mount input dirs also into docker build context [\#61](https://github.com/InfraBox/infrabox/issues/61)
- merge nginx, auth and docker-registry in one pod [\#58](https://github.com/InfraBox/infrabox/issues/58)
- dont show secret value field [\#54](https://github.com/InfraBox/infrabox/issues/54)
- unify cloudsql/postgres credential secrets [\#53](https://github.com/InfraBox/infrabox/issues/53)
- quotas [\#48](https://github.com/InfraBox/infrabox/issues/48)
- use network policies [\#47](https://github.com/InfraBox/infrabox/issues/47)
- hide token values in UI [\#46](https://github.com/InfraBox/infrabox/issues/46)
- configureable tag for deployments [\#45](https://github.com/InfraBox/infrabox/issues/45)
- sort order of builds is broken [\#44](https://github.com/InfraBox/infrabox/issues/44)
- query status of build job via CLI [\#43](https://github.com/InfraBox/infrabox/issues/43)
- full build log download [\#41](https://github.com/InfraBox/infrabox/issues/41)
- deployment share for build artifacts [\#40](https://github.com/InfraBox/infrabox/issues/40)
- configurable timeout per job/build [\#39](https://github.com/InfraBox/infrabox/issues/39)
- infrabox pull cannot pull containers that failed [\#38](https://github.com/InfraBox/infrabox/issues/38)
- replace flask with bottle [\#37](https://github.com/InfraBox/infrabox/issues/37)
- move request validation into github container [\#36](https://github.com/InfraBox/infrabox/issues/36)
- rewrite github-review [\#35](https://github.com/InfraBox/infrabox/issues/35)
- insert modified files [\#34](https://github.com/InfraBox/infrabox/issues/34)
- Icons in Branch History are not intuitive [\#31](https://github.com/InfraBox/infrabox/issues/31)
- Semantic URLs for easier reference [\#30](https://github.com/InfraBox/infrabox/issues/30)
- automatic database migration [\#29](https://github.com/InfraBox/infrabox/issues/29)
- job QoS should be guaranteed [\#26](https://github.com/InfraBox/infrabox/issues/26)
- Internal Server Error for PR synchronize [\#25](https://github.com/InfraBox/infrabox/issues/25)
- infrabox run not possible [\#24](https://github.com/InfraBox/infrabox/issues/24)
- document generator [\#23](https://github.com/InfraBox/infrabox/issues/23)
- Submit job with --job [\#22](https://github.com/InfraBox/infrabox/issues/22)
- Containers aren't cleaned up after failed build [\#21](https://github.com/InfraBox/infrabox/issues/21)
- Github connect button does not work \("Add New Project"\) [\#18](https://github.com/InfraBox/infrabox/issues/18)
- error output dependencies [\#14](https://github.com/InfraBox/infrabox/issues/14)
- single job restart [\#12](https://github.com/InfraBox/infrabox/issues/12)
- copy\_files [\#11](https://github.com/InfraBox/infrabox/issues/11)
- rename kube-scheduler [\#8](https://github.com/InfraBox/infrabox/issues/8)
- rename api-server [\#7](https://github.com/InfraBox/infrabox/issues/7)
- remove commit\_after\_run [\#6](https://github.com/InfraBox/infrabox/issues/6)

**Merged pull requests:**

- Update gcs.md [\#119](https://github.com/InfraBox/infrabox/pull/119) ([ib-steffen](https://github.com/ib-steffen))
- Docs [\#118](https://github.com/InfraBox/infrabox/pull/118) ([ib-steffen](https://github.com/ib-steffen))
- fixes [\#116](https://github.com/InfraBox/infrabox/pull/116) ([ib-steffen](https://github.com/ib-steffen))
- minor ui improvements [\#115](https://github.com/InfraBox/infrabox/pull/115) ([ib-franziska](https://github.com/ib-franziska))
- Compose [\#105](https://github.com/InfraBox/infrabox/pull/105) ([ib-steffen](https://github.com/ib-steffen))
- some minor ui fixes [\#100](https://github.com/InfraBox/infrabox/pull/100) ([ib-franziska](https://github.com/ib-franziska))
-  Badges and Project Info [\#99](https://github.com/InfraBox/infrabox/pull/99) ([ib-franziska](https://github.com/ib-franziska))
- fixes [\#98](https://github.com/InfraBox/infrabox/pull/98) ([ib-steffen](https://github.com/ib-steffen))
- fixes [\#97](https://github.com/InfraBox/infrabox/pull/97) ([ib-steffen](https://github.com/ib-steffen))
- Select github repo [\#94](https://github.com/InfraBox/infrabox/pull/94) ([ib-franziska](https://github.com/ib-franziska))
- Fixes of fixes of fixes of ... [\#91](https://github.com/InfraBox/infrabox/pull/91) ([ib-franziska](https://github.com/ib-franziska))
- Ingress [\#90](https://github.com/InfraBox/infrabox/pull/90) ([ib-steffen](https://github.com/ib-steffen))
- Login page [\#89](https://github.com/InfraBox/infrabox/pull/89) ([ib-franziska](https://github.com/ib-franziska))
- UI update [\#88](https://github.com/InfraBox/infrabox/pull/88) ([ib-franziska](https://github.com/ib-franziska))
- Fixes [\#87](https://github.com/InfraBox/infrabox/pull/87) ([ib-steffen](https://github.com/ib-steffen))
- Add project page and some other stuff [\#86](https://github.com/InfraBox/infrabox/pull/86) ([ib-franziska](https://github.com/ib-franziska))
- minor fixes [\#85](https://github.com/InfraBox/infrabox/pull/85) ([ib-steffen](https://github.com/ib-steffen))
- Quay [\#84](https://github.com/InfraBox/infrabox/pull/84) ([ib-steffen](https://github.com/ib-steffen))
- Things [\#83](https://github.com/InfraBox/infrabox/pull/83) ([ib-steffen](https://github.com/ib-steffen))
- Next style update dashboard 2.0 [\#81](https://github.com/InfraBox/infrabox/pull/81) ([ib-franziska](https://github.com/ib-franziska))
- Fixes2 [\#80](https://github.com/InfraBox/infrabox/pull/80) ([ib-steffen](https://github.com/ib-steffen))
- Kube resources [\#79](https://github.com/InfraBox/infrabox/pull/79) ([ib-steffen](https://github.com/ib-steffen))
- Layout update [\#71](https://github.com/InfraBox/infrabox/pull/71) ([ib-franziska](https://github.com/ib-franziska))
- more [\#70](https://github.com/InfraBox/infrabox/pull/70) ([ib-steffen](https://github.com/ib-steffen))
- Dashboard 2.0 [\#69](https://github.com/InfraBox/infrabox/pull/69) ([ib-franziska](https://github.com/ib-franziska))
- allow setting capabilities [\#67](https://github.com/InfraBox/infrabox/pull/67) ([ib-steffen](https://github.com/ib-steffen))
- fix installer [\#66](https://github.com/InfraBox/infrabox/pull/66) ([ib-steffen](https://github.com/ib-steffen))
- Fixes [\#65](https://github.com/InfraBox/infrabox/pull/65) ([ib-steffen](https://github.com/ib-steffen))
- unify postgres secrets [\#57](https://github.com/InfraBox/infrabox/pull/57) ([ib-steffen](https://github.com/ib-steffen))
- dont show secret value [\#56](https://github.com/InfraBox/infrabox/pull/56) ([ib-steffen](https://github.com/ib-steffen))
- require dashboard-secret [\#55](https://github.com/InfraBox/infrabox/pull/55) ([ib-steffen](https://github.com/ib-steffen))
- github ignore commits with distinct=false [\#52](https://github.com/InfraBox/infrabox/pull/52) ([ib-steffen](https://github.com/ib-steffen))
- fix job history [\#51](https://github.com/InfraBox/infrabox/pull/51) ([ib-steffen](https://github.com/ib-steffen))
- Open docs in new tab or window [\#32](https://github.com/InfraBox/infrabox/pull/32) ([Steffen911](https://github.com/Steffen911))
- Fix URL to build for PRs [\#28](https://github.com/InfraBox/infrabox/pull/28) ([else](https://github.com/else))
- Remove .\*.swp file, add to .gitignore [\#27](https://github.com/InfraBox/infrabox/pull/27) ([else](https://github.com/else))
- Typo [\#20](https://github.com/InfraBox/infrabox/pull/20) ([Steffen911](https://github.com/Steffen911))
- Cleaned up and renamed getting started page [\#5](https://github.com/InfraBox/infrabox/pull/5) ([ib-franziska](https://github.com/ib-franziska))
- Small fixes [\#1](https://github.com/InfraBox/infrabox/pull/1) ([ib-franziska](https://github.com/ib-franziska))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*