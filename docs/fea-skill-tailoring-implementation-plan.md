# FEA Expert skill iyileştirme ve üç istemci için uygulama planı

21 Kasım 2026 · Başlangıç: `abde60d`, FEA Expert `0.1.5` · Windows, Designcenter `2612.1700`

## Hedef ve başlangıç durumu

39 skill’i modelden bağımsız teknik yönlendirmelere ve gerektiğinde açılan referanslara dönüştür. Eğitim seti ve açık model, genel kuralları sınamak için yerel kanıt sağlar. Dağıtılan skill, tarif ve örneklerden modele özgü dosya ve çözüm adları, kimlikler, yükler, model kabulleri, müşteri şablonları ve konuşma metinleri çıkar. Örnekleri bağımsız ve tekrar üretilebilir sentetik problemlerden kur. AgentsAI, Codex ve VS Code Copilot aynı skill kaynağını ve operasyon sözleşmesini kullansın.

Bu plan, 19 Kasım [istemci planının](codex-vscode-implementation-plan.md) üzerine kurulur. Güncel kurulum giriş noktaları [README’de](../README.md).

| Yüzey | 21 Kasım gözlemi | Uygulama kararı |
|---|---|---|
| Kaynak ve paket | 39 skill, 1 koordinatör, 6 uzman tarifi, 5 host MCP referansı. Kaynak doğrulayıcı 667 kriteri geçti. 43 testin 42’si geçti, Windows symlink testi `WinError 1314` ile atlandı. Aynı kaynak digest’iyle üç istemci arşivi ve kaynak ZIP’i üretildi. | Mevcut omurgayı kullan. Atlanan yol kaçışı testini destekleyen CI hostunda çalıştır. |
| Model Inspection | Aynı canlı `ugraf.exe` oturumunda part, mesh, malzeme, BC ve mesh kalite çağrıları tamamlandı. 14 mesh kalite kaydının 8’i eleman içerdiği halde `qualityCheckedElements=0` döndürdü. Spring kolektöründe sayısal alanlar sıfırdı. | Metrik başına kapsamı ve hesaplanmış eleman sayısını göster. Sıfır kapsama `UNVERIFIED` olarak yansısın. |
| Designcenter Open | İki vendor connector aynı PID’ye bağlandı. Work/display ve dirty state uyuştu. `BaseWork` bir SIM, `SimPart.FemPart` bir `AssyFemPart` döndürdü. Canlı salt okunur journal, assembly kök mesh kolektörlerini, bileşenleri, solution/subcase atamalarını ve sonuç referanslarını okudu. Çalışma başladığında model zaten dirty idi. | SIM → FEM/AFM bağı doğrudan okunur. Assembly kökü ve bileşen mesh’leri ile prototip ve occurrence kimliği ayrı kaydedilir. |
| API keşfi ve sandbox | 2612 MCP’de `dcopen-class-info` altı CAE sınıfını indekste bulamadı. Kurulu Python binding üzerinde CAE çağrıları çalıştı. Geçerli sandbox journal `SUCCESS`, exit 0 ve boş stdout döndürdü. | İndis sonucu, runtime API ve gözlenebilir sandbox davranışı ayrı kanıtlar. İşlem için doğrulanan release, oturum ve hedefi kaydet. |
| Corpus | Designcenter 2612.1700 batch, çalışma kopyalarında 146/146 hedefi açtı ve mesh kolektörü sorgusunu tamamladı. Kapsam 86 FEM, 58 SIM, 2 AFM. FEM ve SIM sayıları eğitim ZIP’indeki birer dosyayı içerir. Bazı eski dosyalar daha uzun açılış süresiyle tamamlandı. 144 doğrudan model dosyasının kaynak ve kopya SHA-256 değerleri eşleşti. | Korpus açılış, bağımlılık ve alan düzeyinde doğrulama için kullanılabilir. Süre aşımını dosya bozulması olarak sınıflandırmadan önce dar kontrol ve uygun zaman bütçesi kullan. |
| Sonuç okuma | Ayrı BatchPost worker ile kopyalanmış bir OP2 için `open → list → close` tamamlandı. `open` girdisi `file`. Listede kullanıcı adı, XML `unique_name`, indeks ve bileşenler ayrı alanlardı. | Sonuç kimliği dosya, loadcase, iteration, quantity, recovery location ve frame ile kurulur. Export ayrıca doğrulanır. |
| Sentetik çözüm | Kurulu Siemens Nastran ile bağımsız bir SOL 101 eksenel çubuk çözüldü. F06 sonlandı. 0,05 mm deplasman, −1.000 N destek reaksiyonu ve 10 MPa eksenel gerilme analitik değerlerle eşleşti. BatchPost OP2’den aynı düğüm ve X bileşeni için mm biriminde CSV üretti ve değer eşleşti. | Bu fixture solver, QoI ve CSV kontrolüne temel olur. CAD, FEM/SIM yazımı ve save/reopen için ayrı fixture gerekir. |
| Siemens Help Server | 2612 talebi 2606 etiketli dokümanlar döndürdü. NXOpen Python, assembly FEM, SOL 401 preload/subcase, EIGRL ve shell post-processing için 2606 teknik kaynakları bulundu. | İstenen sürümü, döndürülen doküman sürümünü ve sınanan runtime build’ini ayrı kaydet. |

Kaynak paketleri `SOURCE_ONLY` seviyesindedir. İki yerel connector’da canlı okuma yapıldı. Üç istemcinin taze sohbetinde keşif ve uçtan uca yeterlilik, paketleme işinin kabul adımlarıdır.

## 1. Kaynak denetimi ve skill sahipliği

**P0.** Kanonik envanteri `git ls-files` ile çıkar. Denetime skill girişlerini, referansları, scriptleri, tarifleri ve istemci talimatlarını dahil et. Üretilmiş aynaları, geçmiş kurulumları ve receipts’i kaynak envanterinin dışında tut. Her karar için mevcut satır, eylem, hedef dosya, kanıt ve regresyon senaryosu kaydet.

- **KEEP** · Etkin solver set ID, yük yolu, frame/birim, bağımsız readback, yetki ve provenance gibi FEA’ya özgü kararları koru.
- **NARROW** · Açıklama, kullanıcının hangi işleminde skill’in devreye gireceğini söylesin. Root belge karar ve ilk işlem için gerekenleri taşısın. Bilinen katalog ve model bağını yeniden keşfetme şartını kaldır.
- **RELOCATE** · API imzası, sürüm farkı, formül varsayımları ve uzun XML’leri dar referanslara taşı. Tarihsel yeterlilik ve vaka kanıtı paket dışı kayıtlarla izlenir.
- **REMOVE** · Model adı ve numaraları, modelden taşınmış varsayılan parametreler, eğitimdeki istasyon/subcase sayıları, müşteri şablonları, konuşma ve geçmiş pilot kodları skill, tarif, script varsayılanı ve referanslardan çıkar. Teknik içerik kaynak ve anlam korunarak yeniden yazılır.
- **UNVERIFIED** · İlgili miktarı, API’yi veya akışı ve eksik kanıtı açık yaz. Tarihsel başarıyı başka release, model, host veya yönteme taşımadan önce eşleşmeyi sına.
- 13 entegrasyon skill’indeki ortak güvenlik bloğunu tek çalışma sözleşmesine indir. Host allowlist’i, controller politikası, mutasyon preflight ve bağımsız readback ile uygulanmaya devam etsin. Tarifteki koşulsuz manuel save talimatlarını, doğrulanmış resmi save yolu veya gerektiğinde operatör kaydı ve reopen kanıtı olarak modelle.
- Önce/sonra için açıklama boyu, girişlerin p50/p90 boyu, tekrar eden bloklar, görev başına açılan skill/referans ve yanlış rota sayısını ölç. İlk sürümde 39/39 giriş için en az bir pozitif tetikleme örneği, çakışan rotalar için negatif örnek tanımla.

[OpenAI Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

### 39 skill için değişiklik matrisi

| Alan | Skill yolları (`skills/` altında) | İlk karar ve kabul |
|---|---|---|
| Yönlendirme ve native işlem | `fea-chief-engineer`, `fea-sc3d-tool-routing`, `fea-native-runtime-gate` | **NARROW/KEEP.** Genel çalışma, araç yönlendirme ve mutasyon/readback sözleşmesinin sahipliğini belirle. Aynı bağlamda katalog ve model kimliği tekrar istenmesin. Belirsiz etki sonraki işlemi bloke etsin. |
| NXOpen | `designcenter-open-connection-status`, `designcenter-open-api-discovery`, `designcenter-open-documentation-search`, `designcenter-open-journal-authoring`, `designcenter-open-model-data-read` | **NARROW/RELOCATE/UNVERIFIED.** İndis, Python dokümanı ve kurulu binding ayrımı. Bilinen operasyonda koşulsuz 8 adımı kaldır. CAD extraction schema ve CAE object access için ayrı rotalar. Derlenmiş script yerine gözlenebilir sandbox çıktısı veya açık kanıt limiti. |
| Model Inspection | `simcenter-3d-connection-status`, `simcenter-3d-material-and-body-inspection`, `simcenter-3d-mesh-inspection`, `simcenter-3d-mesh-quality-review`, `simcenter-3d-mesh-generation`, `simcenter-3d-simulation-boundary-conditions`, `simcenter-3d-visibility-and-selection` | **NARROW/KEEP.** Katalogdan scope ve filter kombinasyonlarını doğrula. Boş filtreyle tüm varlıkları etkileme koşulunu açık yaz. Sıfır metrik kapsamı ve boş BC bağlamı için regresyon. |
| Modelleme | `fea-model-preparation`, `fea-open-meshing`, `fea-mesh-quality`, `fea-materials-properties` | **RELOCATE/REMOVE.** İçe aktarılan model anlatısını idealizasyon, associativity, unit scale, shell yönü, collector/property/material sahipliği ve yük aktarımı kararlarına çevir. Mesh varlığı, geometrik kalite ve QoI yakınsaması ayrı kontroller. |
| Yük aktarımı ve malzeme fiziği | `fea-connector-contact`, `fea-multistep-nonlinear`, `fea-continuum-thermomechanics`, `fea-thermal`, `fea-composite-laminates` | **KEEP/RELOCATE.** Preload/lock/service, contact, temperature reference ve laminate frame/stack kurallarını doğru uzmanlığa taşı. Sentetik örnekle işaret, kuvvet/enerji dengesi ve yanlış temas durumunu sınay. |
| Dinamik ve dayanım | `fea-dynamics`, `fea-modal-correlation`, `fea-random-response`, `fea-durability` | **KEEP/NARROW.** Free-free, prestressed modal, harmonic, transient, stationary PSD ve signed fatigue history için ayrı önkoşullar. DOF/frame eşlemesi, rigid-body altuzayı, repeated roots ve state kapsamı. Tarihsel fixture atıflarını temizle. |
| Solver ve çözüm kurulumu | `simcenter-nastran`, `fea-solver-investigation`, `fea-artifact-forensics`, `simcenter-parametric-sol101` | **NARROW/RELOCATE/REMOVE.** Deck ve etkin set çözümleme, çözüm yürütme ve arşiv forensics için birincil sahipler. Cantilever pilot’unu genel parametrik SOL 101 ve ayrı sentetik benchmark’a dönüştür. |
| Sonuç ve kabul | `batchpost-actions`, `fea-results-interpretation`, `fea-vvuq-review`, `fea-acceptance-verifier` | **KEEP/RELOCATE.** Format sözleşmeleri ve sonuç kimliği korunur. Layer, frame, recovery ve averaging kontrolleri gerektiğinde okunur. Solver sonucunu bağımsız QoI ve rapor artifact’iyle bağla. |
| Aerostructures | `simcenter-airframe-structural-verification`, `simcenter-aerostructures-load-filtering`, `simcenter-aerostructures-margin-of-safety` | **REMOVE/RELOCATE/UNVERIFIED.** Eğitim hiyerarşisi, SOL 144 model adları, station/case sayıları, LCF solution adı ve şirket Word şablonu çıkar. Genel GFEM/aero bağlantısı, kuvvet-moment frame, envelope/LCF, allowable/MoS provenance korunur. ABB, Knowledge Fusion ve Report Writer iddiaları ürün/release bazında sınanır. |

## 2. Corpus, Siemens Help ve API doğrulaması

**P0.** Her dosya için hash, part türü, release, açılış, unloaded bağımlılıklar, birim, CAD/FEM/AFM bağlantısı, collector/mesh, solution/subcase, BC descriptor, sonuç referansı ve alan hatalarını kaydet. Aynı hedefe ait denemeleri tek kayıtta ilişkilendir. Model kimliği ve ham çıktılar yerel çalışma alanında kalır. Genellenen bulgu, paket referansına bağlanabilir.

Korpus 58 çözüm ve sekiz solution descriptor döndürdü. Dört çözümde BC yalnız subcase düzeyinde, 57 SIM’de sonuç referansı vardı. 12 kayıtta bildirilen CAD yolu diskte çözülemedi. Bir SIM’de genel BC envanteri native erişim hatası verdi, çözüm/step okuması tamamlandı. Bu gözlemler; alan bazında başarı, solution ve subcase kapsamı, dependency path kontrolü ve sonuç referansı ile gerçek artifact ayrımı için regresyon senaryolarına dönüştürülmeli.

| İş | Uygulama ve kabul |
|---|---|
| CAD → FEM/AFM → SIM | `SimPart.FemPart`, `BaseFemPart.BaseFEModel`, `AssyFEModel.GetChildren` ve `FEModelOccurrence.GetChildren` için tür, çağrı ve örnek kapsamı. Tek FEM, AFM ve nested occurrence, eksik bağımlılık, CAD bağı olmayan FEM. Occurrence transform ve label offset kaynakları ayrı doğrulanır. |
| Mesh ve malzeme | `MeshManager.GetMeshCollectors` ve collector mesh’lerini Model Inspection ile karşılaştır. Boş koleksiyon, unsupported metrik ve başarısız read ayrımı. 1D/2D/3D karma modeller, mesh quality paydası, property table ve malzeme ataması. |
| BC ve load | `Loads/Constraints/SimulationObjects` envanteri, `SimSolution.GetBcs()` ve `GetStepByIndex(i).GetBcs()` atamaları. Etkin deck üzerinden case control, set referansları ve lokal frame çözülür. Pasif tanım, boş scope, çoklu subcase ve preload da sınanır. |
| Deck, sonuç ve state | Seçili DAT/F06/OP2 kanıtını tam solution/state ve dosya hash’i ile bağla. BatchPost `open → list → export → close`, gerçek CSV/plot ve sayı/etiket kontrolü. Arşiv sonuç dosyası ile yeni native solve ayrımı. |
| Mutasyon | Yeni sentetik çalışma kopyası ve izole oturumda resmi MCP üzerinden geometri, mesh, BC ve çözüm ekleme. Aynı GUI oturumunda seri çağrı. Yetki, hedef, pre/postcondition, schema ve payload hash’i. Timeout ve belirsiz sonuçta taze readback; persistence için yeni ad, dosya kimliği ve bağımsız reopen. |

Her API kaydı `intent, owner/type, member, source/release, profile/schema, precondition, witness, failure/fallback` taşır. Bilinen operasyon için doğrulanmış 2612 kaydını başlangıç al. Yeni kabiliyet için hedefli keşif, ilgili resmi Python referansı, kurulu binding’de dar salt okunur prova ve gereken etki testi uygula. API indeksindeki boş sonucu indis kapsamı olarak kaydet. Help Server tam sayfa isteği başka bir konu döndürürse kanıtı gerçekten eşleşen arama sonucu ve başlıkla sınırla. Sandbox boş stdout durumunda, varsa doğru worker ve tanık ile sistem-log doğrulaması yürüt. Beklenen değer ve davranış için ayrıca gözlenebilir çıktı gerekir.

### Siemens teknik dayanakları

- FEM associativity, CAD bağlantısı ve BC mapping’i doğrula. Assembly içindeki bileşenlerin associativity durumu farklı olabilir. [Associative FEM](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/id967840?audience=external) · [Assembly FEM workflows](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/id623176?audience=external) · [Replace FEM](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.design/html/id624506?audience=external)
- `.afm` ayrı NXOpen part türüdür. Result reference ve BC’lerin okunması solution/subcase bağlamını gerektirir. [NXOpen Python AssyFemPart 2606](https://docs.sw.siemens.com/documentation/external/PL20251024323638784/en-US/custom_api/nxopen_python_ref/a26413.html) · [NXOpen Python SimSolution 2606](https://docs.sw.siemens.com/documentation/external/PL20251024323638784/en-US/custom_api/open_python_ref/a34617.html)
- SOL 401’de yük, kısıt, temas ve bağımlı zaman adımlarını subcase sırasıyla kontrol et. SOL 401/402 preload için geçerli case-control ve kartı eşleştir. [SOL 401 subcase sequencing](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2190749?audience=external) · [Preload subcase](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid2116881?audience=external)
- EIGRL aralık, root sayısı ve normalizasyonu deck/F06 ile bağla. Shell top/bottom, recovery location ve nodal averaging sonuç kimliğine girer. [EIGRL](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.QRG/html/id508036?audience=external) · [Shell elemental results](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.design/html/xid2285444?audience=external) · [Result averaging](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.design/html/xid1398288?audience=external)

Aerostructures, composite, PSD ve fatigue için korpusun kapsamadığı her iddia ayrıca uygun Siemens kaynağı ve sentetik veya yetkili fixture ile test edilir.

## 3. Sentetik testler ve mühendislik kabulü

**P1.** Aday skill’ler için işlem ve mühendislik kabulünü küçük, bağımsız problemler üzerinde doğrula. Toleranslar fixture’ın fiziği, ölçeği ve discretization’ına bağlıdır.

| Senaryo | Kabul kanıtı |
|---|---|
| SOL 101 eksenel çubuk ve parametrik kiriş | Kuvvet/reaksiyon dengesi, çubukta `FL/EA` ve `F/A`, kirişte uygun narinlik ve BC altında Euler–Bernoulli. Parametre değişiminde semantic selection ve yeni sonuç hash’i. |
| SOL 103 serbest ve kısıtlı modal | Destek ve mass ownership, bağlı serbest 3B yapıda beklenen rigid-body altuzayı, signed eigenvalue ve modal deplasman kapsamı. Bağlı/ayrık modeller ve repeated roots için altuzay testi. |
| Shell, kalite ve mapped load | Shell katmanı ve frame, 2D/3D kapsamı, yük/ısı akısı aktarımında kuvvet-moment veya enerji korunumu. Bilinçli kötü mesh ve hesaplanmayan metrik. |
| Preload, contact ve termal | Etkin subcase ve preload locking, temas açıklığı/stick/slip, artımlı enerji/reaksiyon. Termal referans, sıcaklık haritası ve malzeme sahipliği. |
| Hatalar, sonuç ve rapor | Eski OP2, yanlış frame/birim, yanlış/eksik/ekstra state, boş sandbox sonucu, stale revision, geç gelen export. Belirsiz işlem otomatik replay edilmez. Doğru çıktının sayısı, etiketi, görseli ve istenen dosya formatı kontrol edilir. |
| İleri uzmanlık | Aerostructures/MoS, composite, correlated PSD ve fatigue için probleme özgü fixture ve bağımsız karşılaştırma. Doğrulanmış release/solver sınırı açıkça kaydedilir. |

`SOURCE_TESTED / FILES_VERIFIED / HOST_DISCOVERED` dağıtım gözlemlerini ve `NATIVE_READ / NATIVE_EFFECT / PERSISTED / SOLVER_VERIFIED / ENGINEERING_ACCEPTED` operasyon gözlemlerini ayrı alanlar olarak kaydet. Mevcut evidence class tüketicileri için geriye uyumlu eşleme kullan. Her kayıt claim kapsamı, durum ve evidence pointer taşır.

## 4. Üç istemci için paket mimarisi

**P1.** Mevcut proje/bundle kurulumlarını destekle. `skills/` tek kanonik içerik olsun. Başlangıç commit’inde kök `plugin.json` yok. Agent Plugins 1.0 manifestini eklerken kimlik, sürüm, açıklama, lisans ve yayıncıyı `.sim-ai-agents.toml` ve tariflerle doğrula. Repo içindeki üretilmiş skill aynalarını önleyen mevcut denetimi marketplace klasörüne izin verecek şekilde daralt. `validate_distribution.py`, `build_distribution.py` ve `package_release.py` aynı yeni dosyaları ve paket yollarını tanısın. Project installer’ların mevcut receipt, yedek ve rollback davranışını regresyon testleriyle kapsa.

| Kanal | Çıktı | İstemci kabulü |
|---|---|---|
| AgentsAI / Simcenter Agent Workspace | Bundle ZIP + TOML sidecar. 1+6 tarif ve beş host `type: ref`. | İzole productdata ile gerçek CLI validate, install ve readback. Taze sohbette agent seçimi, skill yükleme, MCP allowlist ve temsilî uzman yönlendirmesi. Bundle ve proje aynası çakışması test edilir. |
| Codex | Mevcut project ZIP ve işaretli `AGENTS.md` uyumluluk yolu. Portable manifestin `extensions.com.openai` alanı ve gerektiğinde `.codex-plugin/plugin.json` uyumluluk manifesti. Repo kataloğu `.agents/plugins/marketplace.json`; release girdisi immutable tag/commit ile sınanır. | Fresh app-server/desktop chat. Plugin ve proje aynası keşif testi. `qualify_codex_readonly.py` ile aynı backend PID, work/display kimliği, doğru skill ve native payload. |
| VS Code GitHub Copilot | Mevcut `.github/agents` ve `.github/skills` yolu. Portable yol için `com.github.copilot/agents/` ve istemcinin desteklediği marketplace şeması. | Extension/harness sürümü, fresh chat, custom agent, efektif tool allowlist, canlı Model Inspection ve BatchPost sonucu. Paket ve proje kaynaklı çift discovery ile rollback kontrolü. |
| Ortak | `package_release.py` tek staged kaynaktan adayları, ayrı kanal digest’lerini, SHA-256 ve dağıtım manifestini üretir. | Determinizm, canonical skill parity, paket link closure, config koruma, idempotent install, rollback, upgrade ve NX/FEA birlikte keşif. Vendor binary, credentials ve eğitim içeriği paket kapsamı dışında kalır. |

Host’taki global Siemens bağlantılarını kullan. Product Support / Siemens Help Server alias’ını efektif katalogdan bağla. BatchPost worker’ın kendi pipe ve yaşam döngüsünü koru. Kanal kanıtında aday/kanal digest’leri, host/harness, ürün build’i, efektif şema ve yeni sohbet gözlemi bulunsun.

Çapraz istemci tekrarında tek senaryo manifesti kullan. Her pakette en az açık SIM inceleme, yanlış profile yönelme, CAE indisinde olmayan API, sandbox boş çıktı, sentetik solver ve export sorguları çalışsın. Beklenen route ve gözlenen payload’ı eşleştir. Tool namespace ve UI sahipliği kanala göre değişebilir. Sonuç kimliği, hesaplanan QoI ve üretilen artifact karşılaştırması ortak kalır.

[Agent Plugins 1.0 şeması](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) · [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins) · [VS Code Agent Plugin authoring](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference) · [VS Code MCP configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)

## 5. Birleştirme sırası ve çıkış ölçütleri

| Dalga | Teslim | Çıkış ölçütü |
|---|---|---|
| 1 | 39 skill denetimi, corpus raporu ve model bağımsız içerik | 39/39 giriş için karar ve regresyon. 146/146 hedef için native okuma veya dosya bazında somut hata. Repo ve paketlerde model kimliği, eski pilot gömüsü, görev konuşması ve gereksiz tekrar denetimi. |
| 2 | API referansları, sentinel’lar ve sentetik fixture’lar | Assembly scope, mesh kalite kapsamı, BC/subcase, boş çıktı ve yanlış frame için testler. Sentetik modelde native işlem, save/reopen ve bağımsız solver/QoI ayrı kabul satırlarında. |
| 3 | Üç kurulum arşivi ve portable plugin adaptörleri | Windows/Ubuntu kaynak CI, üç izole kurulum, fresh-chat discovery, MCP profil doğrulaması ve rollback. |
| 4 | Çapraz istemci yeterlilik kaydı | Aynı aday ve fixture üzerinden 3/3 istemci kabulü. Normal ve negatif senaryolarda doğru route, model/sonuç kimliği, bağımsız readback ve artifact parity. Release ve operasyon sınırları belgelenmiş. |

İlk PR, kaynak temizliği ile deneyde gözlenen model okuma, BC ve mesh kalite kapsamını birleştirir. Sonraki PR’lar native API/fixture ve paket değişikliklerini ayrı doğrular. Yayıma hazır adayda çözülemeyen claim, hangi veri veya ürün kabiliyetine bağlı olduğunu gösterir.
