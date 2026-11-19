# Simcenter 3D FEA Expert için Codex ve VS Code uygulama planı

19 Kasım 2026 · Windows · Designcenter 2612 içindeki Simcenter 3D Pre/Post

Bu belge başlangıç planını saklar. Uygulamadaki kurulum komutları, MCP davranışı ve aday çıktılar için [README](../README.md) günceldir.

Mevcut AgentsAI bundle’ıyla aynı FEA kaynaklarından Codex ve VS Code GitHub Copilot dağıtımları üretilecek. NX Expert’ın kurulum, paket kimliği, resmi MCP bağlantısı, sandbox ve controller akışı temel alınacak. İlk kurulum ve canlı kabul Codex’te yapılacak. Ardından aynı aday kaynak digest’iyle VS Code ve AgentsAI ayrı oturumlarda doğrulanacak.

## Başlangıç durumu

| Kaynak | Gözlem |
|---|---|
| FEA Expert, `21046e2`, v0.1.2 | 38 kanonik beceri, bir koordinatör ve altı alt tarif. Beş host MCP referansı, yerel vendor connector kopyası içermeyen bundle. Bu çalışmada 9 kaynak testi ve 500 kriterli dağıtım doğrulaması geçti. Tarihsel 78 test farklı kaynak/fixture kapsamına ait. [README](../README.md) · [0.1.2 yeterlilik kaydı](qualification/0.1.2.md) |
| NX Expert kaynak referansı | NX Expert 0.8.0, paket kimliği, proje kurucuları ve controller için referans sürümdür. CAD rutinlerinin native kanıtı kendi çalışma kapsamına aittir. |
| NX Expert kanal kimliği | Proje aynası ile Copilot paketi farklı digest kapsamlarına sahiptir. FEA dağıtımı aday kaynak digest’i ile kanal digest’lerini ayrı tanımlar. |
| AgentsAI kurulu kaynak | `productdata/simcenter-3d-1.0.5-canary.54/mcps.json`, üç launcher ve kurulu FEA/NX paketlerinin `mcps.json` dosyaları incelendi. FEA ve NX paketlerinin vendor MCP tanımları boş, tarifler host’a `type: ref` ile bağlanıyor. Kurulumun seçtiği Designcenter 2612 dizininde üç gerekli ürün binary’si mevcut. |
| Codex yerel adaptör | `.codex/integrations/designcenter/` içindeki `launch.py`, `catalog_startup.py`, `sandbox_result_guard.py`, dokümantasyon ve test kaynakları incelendi. Bu adaptör NX Expert GitHub arşivinin dışında, workstation kurulumuna ait. |
| Canlı çalışma | Başlangıç incelemesi süreç ve kaynak envanteriyle sınırlıydı. Bağlantı, pipe, lisans ve model kimliği her istemcide canlı olarak doğrulanır. |

## AgentsAI MCP topolojisi

| AgentsAI referansı | Kurulu launcher ve runtime | Codex / VS Code görevi |
|---|---|---|
| **Designcenter Open** | `designcenter-open/launch-designcenter-mcp.bat` → `%UGII_BASE_DIR%\UGII\dcmcpserver\DcMcpServer.exe --server designcenter` | Var olan `designcenter` bağlantısını tekrar kullan. NXOpen API discovery, pattern/semantic/keyword search, CAD model şeması ve readback, snippet/journal sandbox, izinli live execute. CAE journal giriş noktaları ve NXOpen.CAE erişimi 2612’de kanıtlanır. |
| **Simcenter 3D / Model Inspection** | `model-inspection/launch-simcenter3d-mcp.bat` → aynı binary ile `--server simcenter3d` | Ayrı client namespace, örneğin `simcenter3d`. Part/body, malzeme, mesh, mesh kalite ve BC/load sorguları. Mesh oluşturma ile görünürlük/seçim işlemlerini etki ve izin açısından ayrıca ele al. |
| **Batch Post** | `batchpost/launch-batchpost-mcp.bat` → `%UGII_BASE_DIR%\NXBIN\sc3d_batchpost_mcpconnector.exe`. Ayrı `sc3d_batchpost.exe --mcp` worker’ı ve varsayılan `sc3d_batchpost` pipe’ı. | `batchpost` bağımsız post-process bağlantısı. Connector startup, worker erişimi, sonuç dosyası açma ve gerçek export ayrı kanıtlar. |
| **Product Support**, **Simcenter Nastran MCP** | FEA tariflerinin kullandığı ek host referansları. | Dokümantasyon ile deck/F06/contact log adli incelemesi. Varsa halihazırdaki yetkili bağlantıları kullan. Nastran dosya erişimi ve allowed roots doğrulanır. Bu araçlar 2612 native CAE yetkisi vermez. |

İlk iki profil aynı binary ve ürün kökünü paylaşır. Yerel AgentsAI manifestinde `UGII_BASE_DIR=C:\Siemens\Designcenter2612` ve ilk iki profil için `DC_CONNECT_TIMEOUT=10000` görülüyor. Launcher’lar ek argümanları geçiriyor, kurulu manifest `--pipe-name` override’ı kullanmıyor. Codex’in NX launcher’ı `MCP_SERVER=designcenter` değerini `--server` argümanına çeviriyor. Aynı launcher’ın `MCP_SERVER=simcenter3d` ile ikinci profile bağlanması ilk doğrulanacak yapılandırmadır. Kullanıcı UI’dan iki profili açtığında her profili kendi namespace ve durum aracıyla keşfet. Profillerin aynı hedef modele bağlandığını canlı kimlikle kanıtla.

Rota seçimi rol → mevcut namespace → ilan edilen araç → exact input schema üzerinden yapılır. Her iki profilde `dc_connection_status` adı görülebilir. Designcenter Open’da önce `explore-model-structure`, ardından gözlenen şemayla `read-model-data` çağrılır. FEM/SIM verisi Model Inspection’a gider. `PAGE` ve `CURSOR` yalnız ilan edilen şemada varsa kullanılır. Mevcut kaynak katalog kaydında BC/load/solution yazımı, save ve solve/submit ilan edilmemiş. Yeni oturumda bunların her biri için ayrı capability ve lisans kanıtı gerekir. [FEA araç matrisi](../skills/fea-sc3d-tool-routing/references/tool-matrix.md)

## NX Expert’tan alınabilecekler

| Parça | FEA uyarlaması |
|---|---|
| Dağıtım ve CI — `package_bundle.py`, `package_release.py`, `build_distribution.py`, `validate_distribution.py` | Tek kaynak envanteri, deterministik ZIP, immutable sürüm, hash manifesti, tam ZIP üye/kapanış doğrulaması, aday staging, native yayın kanıtı. NX yarışmasının 30 dakika kapısını FEA’ya taşımak yerine seçilmiş CAE ve BatchPost fixture’larının ölçülebilir kabulünü kullan. |
| AgentsAI install ve Codex proje sync — `install_bundle.py`, `sync_project_runtime.py`, proje şablonları | CLI list/enable/readback, canonical arşivden `.agents/skills`, kısa `AGENTS.md`, varsa işaretli prompt addendum, yedek ve receipt. FEA’nın mevcut installer’ı önce bundle ID’yi disable ediyor ve sonra hydrate ediyor. Yeni akış aday doğrulamasını önce yapar, enable başarısızlığında önceki durumu geri yükleyebilir ve hydrate gerekiyorsa yalnız doğrulanmış ZIP üyelerini kullanır. |
| Paket kimliği — `runtime_identity.py`, package manifest ve receipt | Ortak aday kaynak digest’i, kanal bazında dosya ve arşiv digest’leri, tam kök seçimi ve `FILES_VERIFIED`. Aynı version string’iyle başka bir proje ya da eski bir checkout’a düşmeyi engelle. |
| Yerel Codex launcher — `launch.py`, `catalog_startup.py`, `sandbox_result_guard.py` | Bir resmi child bağlantısında bounded startup refresh, ilk status-only liste, `tools/list_changed`, diagnostics ve sandbox koruması. Exact request ID ve katalog descriptor’ları korunur. `EXECUTION_FAILED` açık hata, `EXECUTION_UNVERIFIED` eksik gözlenebilir çıktı için. Guard ham yanıtı saklar. BatchPost için ayrı worker readiness gerekir. |
| Resmi bağlar — `official_host_adapter.mjs`, `official_mcp_adapter.py`, `operation_executor.py` | Mevcut host tool dictionary veya erişilebilir mevcut MCP ClientSession. Host bunu sunmazsa CLI prepare/observe ve aynı sohbette doğrudan ilan edilen resmi araç çağrısı. Ad, schema, model ve session değişirse yeniden bağla. Adapter oluşturulurken server veya native işlem başlatılmaz. |
| Sandbox/payload — `payload_contract.py`, `payload_builder.py`, `response_codec.py` ve sandbox notları | AST preflight, strict UTF-8/BOM ve JSON escaping, normalized payload hash, `main(args)`, builder cleanup, native hata, lisans, null ve boş stdout ayrımı. CAD’deki `python_code` ve return kontratını 2612 CAE sandbox’ında minimal pozitif ve zararsız negatif probe ile doğrula. Build’e göre import, builtin, file/save/undo kısıtlarını belgeye bağla. |
| Controller — `run_controller.py`, `step_gate.py`, `execution_preflight.py`, `native_readback.py`, `replay_journal.py` | Kimlik ve hash bağlı hazırlık, sıra, raw response, atomik checkpoint, her adımdan sonra bağımsız native ölçüm, kalıcı UNKNOWN ve scoped replay. NX feature/pose/solid sayısı yerine owner, revision, FEM/SIM, mesh, BC, çözüm ve QoI tanıkları. |
| Runtime bütçesi — `run_budget.py`, `call_bound.py`, `run_timing.py`, bounded lookahead | Göreve bağlı bütçe, ilk kabul zamanı, monotonic ölçüm, lisans duruşu ve late response. Devam adımını yalnız kabul edilen dependency açar. Solver job admission/polling için ayrı süre ve yaşam döngüsü. |
| Readback ve teslim — NX model extraction, `wireframe_transport.py`, `physical_readback.py`, `native_view_capture.py`, Windows persistence rehberi | Minimal typed query, paging bütünlüğü, kaynak ve model kimliği, birim/frame ve bağımsız tanıklar. Görsel gerekiyorsa native capture ve display restoration. FEM/SIM diske yazma, dosya digest’i ve bağımsız reopen/readback farklı iddialar. |
| Copilot kanalı — `integrations/vscode-copilot`, `package_copilot.py`, `install_copilot.py`, JSONC, route/audit | Native custom agent, byte-identical beceriler, kısa talimatlar, route registry, link/helper/signature audit, MCP scope değerlendirmesi, rollback ve workspace receipt. Kullanıcı MCP tanımları read-only. |
| VS Code batching — `integrations/vscode-move-batch`, `package_vscode_move.py` | İhtiyaç çıkarsa trusted local workspace, path containment, `vscode.lm.invokeTool`, iptal, tek çağrı dizisi ve per-step kabul örüntüsünü al. NX Move’a özel VSIX yalnız ilgili bir FEA ardışık işlem sınıfı ve editör tool görünürlüğü doğrulanırsa uyarlanır. |
| CAD uzmanlıkları — çizim/source packet, feature builders, multibody, Move, alignment, MILP ve geometry verification | CAD→idealize parça veya geometri hazırlığı use case’i olan helper’ları gerekçeli ve fixture ile seç. Yarışma parolaları/fazları, CAD performans hedefleri, özel modeller ve EDR/legacy Java resident bu dağıtıma dahil edilmez. |

Aktarımda dosya/commit/lisans envanteri çıkar. NX Expert MIT ve upstream Apache lisansları taşıyor. Bazı helper’larda Siemens telif bildirimi de var. Kurulu vendor binary’leri, launcher’lar ve dağıtım izni doğrulanmamış içerikler arşive alınmaz. Yerel wrapper için provenans ve paylaşım durumu çözülene kadar davranış sözleşmesi ve bağımsız fixture ile ilerle. Host’a özel yollar, loglar, model ve credentials yerel kalır.

## Uygulama sırası

### 1. Kaynak sözleşmesi ve dağıtım omurgası

1. `skills/` ve `recipes/` kanonik kalır. 38 beceriyi rol bazlı registry’ye bağla. Model Inspector, Journal Author, Solver Diagnostics, Results Post, Verifier ve Product Support rolleri ile mesh, dinamik, aerostructures ve SOL 101 dahil mevcut FEA yeteneklerini kapsa. Gereken becerileri ve referansları istek üzerine yükle.
2. AgentsAI’nın 1+6 tarifini ve beş host referansını koru. Codex ve Copilot’ta aynı rol işlevlerini host-native talimat ve becerilerle uygula. Aynı native oturuma giden tüm çağrıları seri tut. `fea-native-runtime-gate` içindeki EDR, vendor extension ve paketlenmemiş `fea_agent` CLI referanslarını denetle. Resmi SC3D/Designcenter rotası ile harici, koşullu çalışma yöntemlerini açıkça bağla. README’de BatchPost worker/connector ayrımını düzelt.
3. NX kalıbıyla release, proje sync, Copilot build/install ve receipt araçlarını ekle. Çıktılar `agents-artefact-windows.zip` + TOML, `vscode-copilot-windows.zip`, portable source ZIP, `distribution-manifest.json` ve `SHA256SUMS.txt`. Codex aynası aynı AgentsAI arşivinden üretilir. Aday staging üretimi release’ten ayrılır. İlk dağıtım NX Expert gibi proje kurulumudur. Marketplace veya native plugin dağıtımı gerekirse daha sonra aynı kaynaklardan eklenebilir.
4. İşaretli, FEA-owned dosyaları yedekle ve geri alma mekanizması ekle. İlk kabul için ayrı Codex ve VS Code FEA çalışma alanları kullan. NX Expert’ın var olan proje köklerinde veya kullanıcıya ait konfigürasyonlarda otomatik migration yapma. Ortak bir workspace gerekirse generated ownership ve duplicate discovery’yi önce audit et.
5. CI’da recipe/skill/MCP refs, JSON/TOML/JSONC, path containment, ZIP determinism, packaged link closure, digest, idempotent tekrar ve rollback testleri çalışır. Source build ve kurulum ne MCP child ne de CAD işlemi başlatır.

**Çıkış:** Üç kanal aday ağacı üretiliyor, 38 beceri ve bağımlılıkları paketlerde doğrulanıyor. Aynı aday kaynak digest’i receipt’lerde, kanal digest’leri ayrıca mevcut.

### 2. Codex’te ilk kurulum ve 2612 read-only kabulü

1. Yeniden kullanılabilir, profil bazlı launcher/doctor hazırla. Açık ürün seçimi, safe child lifecycle, stderr-only log ve bounded katalog. Mevcut Codex kurulumu `DC_CATALOG_WAIT_SECONDS=75`, startup `95 s`, client tool `240 s`, Siemens tool `40 s` kullanıyor. AgentsAI launcher’larda 180 s ve farklı log argümanı var. Parametreleri build’e göre test et. Native işin tamamlandığı sonucunu transport timeout’tan çıkarma.
2. Mevcut `designcenter` bağını mümkünse tekrar kullan. UI’da erişime açılan Model Inspection’ı ayrı namespace ve profil değeriyle ekle. BatchPost’u sonradan worker hazırken aç. Config örneği açıkça seçilen local Windows execution environment’ı hedefler. Installer mevcut global/workspace MCP config’ini yazmaz. [Codex MCP yapılandırması](https://developers.openai.com/codex/mcp)
3. Doğrulanmış arşivi FEA test projesine sync et ve yeni Codex sohbetinde receipt, digest ve `FILES_VERIFIED` kontrolü yap. Expert talimatı ve bir on-demand beceriyi yükle. Her profil için initialize/list, status, actual input schema, delayed `list_changed` ve timeout senaryolarını kaydet. Araç sayısını sabitleme.
4. İki profil üzerinden sırayla taze status ve model kimliği oku. Release, aktif uygulama, work/display part, FEM/SIM lineage, dosya veya managed revision, gözlem zamanı, native session bilgisi varsa onu ve katalog fingerprint’ini kaydet. Küçük CAD okumasıyla FEM/SIM mesh/BC okumasını aynı hedef modele bağla. Kimlik eksik kaldığında mutation gate kapalı kalır.
5. Geometri değiştirmeyen return/echo ve zararsız sandbox negatif kontrolü. Açık çıktı, boş stdout, schema mismatch ve explicit execution error durumlarını kaydet. Host doğrudan tool dictionary sunmuyorsa planlanan CLI prepare/observe yoluyla aynı sohbet aracını çağır.

**Çıkış:** Yeni Codex sohbetinde kurulum, agent/skill discovery, iki profil için fresh model read ve sandbox kanıtı. Bu aşama save, mesh yazımı veya solve içermez.

### 3. CAE controller ve ilk native FEA kabulü

1. Operasyon sözleşmesi `operation_id`, tool role/schema hash, session/model/owner/revision, dirty state gözlemi, etki ve yetki, input ve normalized payload hash, dependency ve ölçülebilir postcondition taşır. Ham MCP zarfı, zaman, lisans ve bağımsız readback her adımın kayıtlarıdır. Part path veya PID tek başına yeterli değildir.
2. Preflight → prepare → official call → raw response → fresh observe → atomik checkpoint. İki profil aynı GUI session’a gidiyorsa aynı seri kuyruğu paylaşır. Controller kilidinin kapsamı dışında kalan diğer host’larla kontrollü fixture’da tek writer kullan. Busy/timeout/cancel/lisans ve yeniden başlatma senaryolarını test et. Belirsiz etki kalıcı `UNKNOWN` ile dependent dispatch’i bloke eder. Taze baseline ve postcondition gözlemi `APPLIED` veya `NOT_APPLIED` kararı verir. Belirsizlik sürüyorsa replay bekler.
3. Sentetik kantilever veya denk bir fixture’ın çalışma kopyasında envanter → ilan edilmiş tek mesh işlemi → bağımsız collector, eleman tipi/count, bölge ve kalite readback’i. Malzeme, BC/load owner, birim/frame ve beklenen model kimliği rapora girer. Bir CAE journal gerekiyorsa ayrı typed schema ve sandbox/native ayrımıyla ekle. Başarı, belirlenmiş postcondition ve mühendislik ölçütüyle değerlendirilir.
4. BatchPost için bilinen ve fixture’a bağlanmış sonuç dosyası kullan. Worker erişimini doğrula. `open → list → export → close`. Loadcase/iteration, quantity, component, unit/frame ve recovery location gözlenir. Yetkili yeni prefix’e CSV ve gerekiyorsa contour üret. Gerçek `written_files`, nonzero boyut, hash, parse, beklenen değer ve close sonucu doğrulanır. Worker yokken canlı mesh envanteri çalışabilir.
5. Save/reopen ve solve ayrı capability gate’leri. İzinli save için yeni FEM/SIM hedefleri ve CAD bağımlılıklarıyla dosya kimliği ve bağımsız reopen. Resmi save yolu yoksa kullanıcı Save As adımı ve ardından bağımsız doğrulama değerlendirilebilir. Sandbox kısıtları korunur. Solve varsa yetkili/lisanslı yol, job ID ve terminal state, deck/F06/OP2 eşleşmesi ve bağımsız QoI gerekir. İlk BatchPost kabulü hazır OP2 kullanabilir. Bu kabul yeni bir solve çalıştırıldığını kanıtlamaz.

**Çıkış:** Bir ölçülebilir native CAE değişikliği, bağımsız readback, belirsiz/başarısız adımda sıfır uygunsuz dependent dispatch ve doğrulanmış BatchPost çıktısı. Kantilever deplasmanı veya reaksiyon dengesi gibi bir bağımsız kontrolle mühendislik sonucu değerlendirilir. Save ve solve ayrı durum alır.

### 4. Aynı adayla VS Code Copilot ve AgentsAI

1. Doğrulanmış AgentsAI arşivinden Copilot ZIP’i üret. `.github/agents/simcenter-fea-expert.agent.md`, `.github/skills`, route/audit, settings/extensions merge ve `.vscode/fea-expert-install-receipt.json`. Gerçek chat içinde agent, beceri ve MCP allowlist gözlenir. Prompt yönlendirmesi, platformun tool approval’ı ve native izin ayrı mekanizmalardır.
2. Copilot harness native `mcpServers` scopes için `$COPILOT_HOME/mcp-config.json` veya workspace `.mcp.json`. Mevcut editor-managed `.vscode/mcp.json` uygun olduğunda forwarding ile değerlendirilir. Scope, namespace, collision, config hash/mtime ve duplicate launcher audit’i. Native Copilot katalog görünürlüğü ile VS Code extension API üzerinden editor-managed görünürlüğü ayrı doğrulanır. [VS Code MCP yapılandırması](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)
3. Yeni Copilot sohbetinde aynı catalog/status, FEM/SIM read, sandbox ve BatchPost fixture’ları. Native yazım için aynı kabul eşikleri. VSIX gerekiyorsa mevcut editor-managed tool’u gerçekten çağırdığını ve ilk başarısız adımdan sonra ikinci çağrı yapmadığını ölç.
4. AgentsAI’da aynı arşivi önce izole productdata’da stage/install/enable et. CLI list, 1+6 tarif, 38 beceri ve host refs. Yeni oturumda seçili role allowlist, native read/sandbox ve BatchPost smoke. Eski enable durumu ve önceki sürüme geri dönüşü test et.
5. Aynı candidate digest ile üç kanalın kabul matrisi tamamlandığında release adayı üret. Rollback prova edilir. Paket veya kurulumun başarılı olması, açık bir sohbetin yeni kodu yüklediğini kanıtlamaz.

**Çıkış:** Kurulum, yeni sohbet discovery, MCP profil ve native fixture kanıtları üç kanalda raporlanmış. Kanal bazında eksik kapsam ve yayın durumu görünür.

## Codex doğrulamasından önce bağlanacak girdiler

- **UI bağları:** Kullanıcının açtığı iki profilin gerçek client adları, hangi Designcenter 2612 oturumuna gittiği ve gerekirse pipe seçimi. Aynı anda birden çok NX/SC3D oturumu varsa her profile doğru hedef bağlanana kadar yazım kapalı.
- **Yerel çalışma alanı ve fixture:** FEA’ya ait test kökü, korunan kaynak ile ayrı çalışma kopyası, küçük FEM/SIM modeli ve bilinen sonuç dosyası. Write/export aşamaları için izinli çıktı dizini ve beklenen FE ölçütleri. BatchPost worker başlangıcı ve lisans kanıtı bu aşamanın girdileri.
- **Dağıtım sahipliği:** Port edilen NX ve yerel launcher dosyalarının lisans/provenans kararı ve hedef kanalların aynı adayı kullanmasını sağlayacak kaynak digest’i. Native solve/save veya VSIX kapsamı ilk keşif ve fixture sonucuna göre karara bağlanır.

## Kabul matrisi

| Kapı | Kaydedilecek kanıt | Bu çalışmanın durumu |
|---|---|---|
| Kaynak ve paket | Commit, source digest, per-file SHA, deterministik çıktı ve paket resource closure | Mevcut FEA kaynak doğrulaması geçti. Yeni dağıtım `NOT_RUN`. |
| Kurulum ve discovery | Kanal receipt, aynı aday kaynak digest’i, gerçek host sürümü, yeni sohbet agent ve skill readback | Yeni FEA kurulumu `NOT_RUN`. |
| Transport ve native okuma | Profil bazlı fresh status, actual schema, taze model/oturum kimliği, CAD ve FEM/SIM okuma | Kurulu profil yapısı incelendi. Live read `NOT_RUN`. |
| Sandbox ve CAE controller | Pozitif/negatif probe, mutation receipt, bağımsız postcondition ve UNKNOWN recovery | `NOT_RUN`. |
| BatchPost, solve, persistence | Worker ve fixture, gerçek export hash/QoI. Ayrı native job ve save/reopen kayıtları | `NOT_RUN`. |
| Mühendislik | Bağımsız referans, birim/frame, tolerans ve sonuç karşılaştırması | `NOT_RUN`. |
