# FEA Expert · Nastran dinamik analiz yöntemleri için uygulama planı

21 Kasım 2026 · FEA Expert 0.1.6 (`f48fcb8`) · Designcenter 2612.1700

Bu plan [39 skill’i kapsayan 0.1.6 çalışmasını](fea-skill-tailoring-implementation-plan.md) dinamik analiz, NVH ve alt yapı yöntemleriyle derinleştirir. Hedef, istenen fiziksel çıktıyı anlayan, doğru ürün ve işlem yolunu seçen ve sonucunu bağımsız bir karşılaştırmayla sınayan bir FEA Expert sürümüdür. Eğitimlerden girdi sözleşmesi, seçim ölçütü, hata koşulu ve doğrulama yöntemi çıkarılır. Dağıtımdaki örnekler bağımsız üretilmiş sentetik problemlerden kurulur.

## 1. Araştırma ve kanıt sınırı

| İnceleme | Gözlem | Uygulama kararı |
| --- | --- | --- |
| Eğitim kapsamı | 117 dosya envanterlendi. 7 sunumda 113 slayt, 10 Word belgesi ve 5 çalışma kitabının metni, tabloları ve hücreleri çıkarıldı. İki bağımsız solver grafiği incelendi. Ofis kilit dosyası ve geçici dosya envanterde tutuldu. | Kaynak–yöntem eşlemesini yerel araştırma kaydında tut. Skill’lere eğitimdeki geometri, etiket, parametre, isim, journal, grafik ve müşteri bilgisi yerine yöntem sözleşmesini yaz. |
| Native modeller | 17 FEM, 5 AFM ve 7 SIM’in hash eşleşmeli kopyaları ayrı 2612 batch oturumlarında açıldı. 29 hedefte mesh collector ve ilgili olduğunda occurrence, SIM→FEM bağlantısı, solution/step BC ve result reference okundu. NX, bu eski dosyaları açınca modified bildirdi. Açılışta unloaded part raporlanmadı. | Model açılışı, aktif atama, haricî sonuç bağlantısı, temiz kayıt ve yeniden açılış için ayrı gözlemler tut. Sonuç referansını fiziksel artifact ve state ile ayrıca bağla. |
| Solver dosyaları | 9 DAT, 6 F06 ve diğer metin dosyalarıyla toplam 49 kayıt tarandı. DAT’larda SOL 103 ve SOL 111 görüldü. 9 DAT’ın 7’sinde mevcut dar parser ilk kapsam dışı kayıtta durdu. 6 F06 sonlanma işareti içeriyor, 5’inde uyarı var. | İleri deck incelemesinde kapsamı ve çözülemeyen kayıtları görünür yap. Yeni solver koşusu ve mühendislik kabulü için arşivdeki sonlanma işaretine ek kanıt iste. |
| Sonuç katalogları | BatchPost 6 OP2’nin tümünü açtı. Beşinde loadcase/iteration vardı. Altıncı OP2, üç RS2 ve bir UNV açıldı ve boş katalog döndürdü. Üç EEF ve bir AFU bu BatchPost yolunda format hatası verdi. UNV metninde fonksiyon dataset’i 58 görüldü. | Açılış, alan kataloğu, fonksiyon/matris kapsamı, export ve QoI denetimi için ayrı kabul ölçütleri kullan. Boş katalogda talep edilen sonuç için uygun okuyucuyu araştır. |
| Canlı 2612 | Designcenter Open ve Simcenter 3D Model Inspection aynı canlı backend’e bağlandı. SIM ve bağlı AFM okundu. NXOpen Response Dynamics manager’ında `EvaluationSettingManager`, `Solutions`, `Events`, `Excitations` ve `Sensors` tip erişimleri tekrarlandı. Açık SIM’e yazım yapılmadı. | Gözlenen tip erişimlerini 2612 salt okunur kataloğuna ekle. Veri alanları, builder işlemleri ve kayıt için ayrı yeterlilik kaydı tut. |
| Siemens dokümanı | Help Server’a 2612 soruldu. İlgili arama kayıtları 2606 serisinden döndü. Beş tam metin sorgusu farklı konu başlığı döndürdü. | Yalnız eşleşen arama kayıtları teknik dayanak olarak kullanıldı. Tam metin iddiası için dönen sayfanın başlık ve sürümünü doğrula. İstenen sürümü, döndürülen sürümü, dil binding’ini ve yerelde çalışan build’i ayrı kaydet. |

Office incelemesi belge ve sunum metni, varsa notlar, tablolar ve hücreleri kapsadı. Gömülü ekran görüntülerinin tamamı piksel düzeyinde incelenmedi. Korpus için yeni solve veya sayısal export yapılmadı. İleri yöntemlerin authoring, save/reopen, solver ve sayısal kabul çalışmaları planın uygulama adımlarıdır. [0.1.6 yeterlilik sınırı](qualification/0.1.6.md)

## 2. Analiz niyetinden rotaya

İlk mesajdan istenen teslimi, fiziksel girdiyi ve çalışma durumunu çıkar. Bilinen bilgileri mevcut bağlamdan kullan. Bir ayrım sonucu değiştirecekse o ayrımı netleştir. Örneğin “ivme spektrumu” için PSD, SRS veya kompleks FRF seçimini çıktı birimi ve beklenen sonuçla yap. Birden fazla yöntemin sırasını fiziksel bağımlılık belirler.

| İstenen çıktı | Birincil yöntem sahibi | Uygulama yönü ve gerekli ayrım |
| --- | --- | --- |
| Normal mod, frekans, etkin modal kütle | `fea-dynamics` | SOL 103. Sınır koşulu, prestress durumu, işaretli kökler, etkin kütle ve normalizasyon. Mod eşleme için `fea-modal-correlation`. |
| Bilinen deterministik uyarımdan kompleks FRF veya harmonik cevap | `fea-dynamics` | Nastran SOL 108 doğrudan veya SOL 111 modal. Hazır mode set / FRF set ile amaca uygun NVH rotasını seç. Girdi force, enforced motion veya load recipe olabilir. |
| Zaman serisi, yük tersinmesi veya signed tensör geçmişi | `fea-dynamics` | Kalifiye transient route. Zaman ekseni ve recovery konumuyla bağla. Girdi yalnız tepe spektrumuysa tam zaman geçmişi için uygun uyarım kaydı gerekir. Yorgunluk için `fea-durability`. |
| Taban hareketi altında tahmini tepe | `fea-dynamics` → SRS | Response Dynamics modal basis, excitation ve response-spectrum event/evaluation. Nastran response-spectrum kurulumunu ayrı solver seçimi ve deck kanıtıyla kullan. |
| Durağan rastgele girdi için PSD/CSD, RMS veya motorun desteklediği diğer random çıktı | `fea-random-response` | Girdi ve yöntem uygunsa SOL 111 random alt durumları. Etkin `RANDOM`, `RANDPS`, `TABRND1`, damping ve output isteklerini birlikte kontrol et. |
| Mode set’e aktarılacak eşdeğer viskoz/yapısal damping | `fea-dynamics` → modal damping | SOL 103 modal projeksiyon ve damping çıktısı, fiziksel mod eşlemesi, mode-set readback. Ölçümden damping fit’i ayrı tanımlama yöntemi. |
| Assembly için dinamik bileşen temsili | `fea-model-preparation` | Tam FEM, mode set, FRF set veya external SE. `fea-dynamics` band ve dinamik kabulü denetler. |
| Doğrudan ölçülemeyen operasyonel kuvvetleri tahmin | `fea-dynamics` → load identification | Ölçülmüş veya hesaplanmış transferler ve operasyonel cevaplar. Uygun stiffness/admittance yöntemi veya çok kanallı ters problem. |
| Kısmen korele referansların bağımsız matematiksel bileşenleri | `fea-dynamics` → NVH PCA | Frekans başına referans CSD matris ayrışımı. Sonraki sentez random response ise `fea-random-response`a geç. |
| Hedef cevapta yapısal ve/veya akustik yol katkıları | `fea-dynamics` → TPA | Uygun transfer ve yük çifti, fazlı birleşim ve bağımsız hedefle rekonstrüksiyon. Yalnız görselleştirme veya tanıda mevcut çıktıyı oku. |
| Eldeki deck, log veya sonuç için köken ve kapsam | `fea-artifact-forensics` | F06 ve etkin kartlar için solver inceleme, alan sonuçları için BatchPost, fonksiyon/temsil için format ve sürüm açısından yeterli native yol. |

[Response spectrum analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/id631266?audience=external) · [Forced response SOL 108/111](https://support.sw.siemens.com/en-US/knowledge-base/KB000155524_EN_US) · [RANDOM case control](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id510121?audience=external) · [Load identification](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1685198?audience=external) · [PCA](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929445?audience=external) · [TPA](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1665256?audience=external)

## 3. Paketlenecek yöntem ve kabul ölçütleri

### Taban uyarımı, SRS ve Response Dynamics

- İvme zaman kaydında örnekleme, başlangıç koşulu, polarite, eksen ve birimi doğrula. SRS eğrisinde frekans, damping, tepe tanımı ve mutlak/pseudo konvansiyonunu kaydet. Spektrum zarfı varsa kaynak eğrileri ve zarf kuralını izle. Modal basis için kısıt, enforced-motion DOF, etkin kütle, recovery alanı ve frekans kapsamını oku.
- Bağımsız tek serbestlik derecesi referansı kur. `z'' + 2ζωₙz' + ωₙ²z = −a_b(t)` ile bağıl yer değiştirmeyi, `z'' + a_b` ile mutlak ivmeyi ve `ωₙ² max|z|` ile pseudo ivmeyi kıyasla. Zaman adımı ve uyarım sonrası sönüm kuyruğunu dene. Çok modlu sentetik durumda modal kombinasyon, yön kombinasyonu ve eksik kütleyi ürün/yöntemle eşleştir. Bir eğitimde görülen SRSS/NRL sıralaması yalnız o çalışmada geçerlidir.
- Native kabul için basis, event, etkin excitation ve evaluation ayarını, yeniden açılıştaki eşleşmeyi ve bağımsız tepe değerini kaydet. Zaman serisi talebi için ayrı transient fixture kullan.
- Modal ve yön kombinasyonu sonrası bulunan tepe büyüklüklerini eşzamanlı tensör bileşenleri olarak kullanma. İstenen nicelik birleşik stress, destek yükü veya reaksiyonsa ürünün recovery ve kombinasyon tanımını doğrudan doğrula.

[Nastran Response Spectrum Analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.basic_dynamics/html/id471026?audience=external) · [Response Dynamics Function Toolkit](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1755918?audience=external) · [Response Spectrum teorisi](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.adv_dyn/html/id475981?audience=external)

### Deterministik forced response ve modal damping

- Kompleks `y = H(f)u` için DOF, yön, birim, FRF türü, faz ve frekans tabanını doğrula. Doğrudan, modal ve mode-set tabanlı çözümleri aynı fiziksel state, damping, frekans ve recovery noktalarında karşılaştır. Modal truncation, residual vector ve frekans inceltmesinin hedef QoI üzerindeki etkisini ölç. Anti-rezonansta sıfıra yakın kompleks cevap için mutlak tolerans kullan.
- Analitik sönümlü osilatörde genlik ve faz, iki DOF’ta frekansa bağlı yük ve modal truncation test et. Load recipe ve UNV girdisinde birim, eşleşmeyen DOF, faz dönüşümü ve çift uygulanan yük hatalarını çalıştır. Alan ve fonksiyon çıktısını aynı çözüm state’iyle bağla.
- Mode set için `MDLDAMP`, `KDAMP` ve varsa rigid-body kesiminin etkisini kart, F06/OP2 ve mode-set readback ile bağla. Viskoz projeksiyon için `bᵢᵢ/(2mᵢᵢωᵢ)` ve yapısal loss factor için `k₄,ᵢᵢ/kᵢᵢ` referans kur. Arayüzün raporladığı büyüklük ve dönüşümü solver ayarıyla doğrula. Mod eşlemede frekans ve MAC, kümelenmiş modlarda altuzay kullan. Kuvvetli modal coupling durumunda diagonal yaklaşımı doğrudan FRF ile kıyasla. Boş damping alanında kaynak fizik ve çıktı isteğini ayrı incele.

[Modal-based frequency response](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1975648?audience=external) · [Mode set theory and damping](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1899327?audience=external) · [Viscous and structural damping values in mode sets](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1875000?audience=external)

### SOL 111 random response ve spektral giriş

- Frekans, birim, tek/çift taraflı spektrum, kanal/DOF ve subcase bağını normalize et. Diyagonal PSD gerçel ve negatif olmayan, çapraz terimler Hermit simetrili, matris tolerans içinde pozitif yarı tanımlı olsun. Sıfır çapraz terim için bağımsızlık varsayımı girdi sözleşmesinde açık olmalı. Interpolasyon ve ekstrapolasyonu kaydet.
- Tabloları önce salt okunur doğrula. Şema kimlik, frame, bileşen, girdi türü, birim, frekans ve real/imag temsilini taşır. Geçerli girdiden solver set planı ve sentetik deck üret. Ardından ilgili 2612/solver descriptor’ında modeling object ve field oluşturmayı kalifiye et. Aynı girdi yeniden işlendiğinde tekrarlı subcase veya kapsam dışı değişiklik oluşmasın.
- Girdi sözleşmesinde her spektrum sütunu veya kayıt `(referans kanal, cevap kanalı, frekans, real, imag)` ile anlam kazanır. Kullanıcı bir üçgeni veriyorsa diğerini eşlenikle oluştur. Her iki üçgen varsa uyuşmazlığı bildir. Kayıt başına tekrar eden frekans ve kanal, boş birim, NaN, karşılığı olmayan kanal ve matrisi bozan interpolasyon için ayrı test kullan. Modeldeki devam eden ID alanına bağlanırken tasarlanan ve oluşan subcase haritasını geri oku.
- `Syy = H Sff Hᴴ` ve tek taraflı çıktı için `RMS = sqrt(∫ Syy,ii df)` ile bağımsız kıyas yap. İki girişli fixture’da korelasyonsuz, aynı fazlı, karşı fazlı ve geçersiz PSD halleri olsun. F06, deck ve OP2 niceliğini aynı subcase’e bağla. RMS, crossing sayısı ve frekans çözünürlüklü PSD ayrı çıkışlardır. Yalnız RMS görüldüğünde PSD eğrisinin kanıtı açık kalır.
- Gerilme tensörü ve eşdeğer gerilme istenirse recovery konumu, bileşen kovaryansı ve solver’ın eşdeğer istatistik tanımı gerekli. Tek tek RMS bileşenlerden türetilen von Mises değerini bağımsız solver kabulü olarak kullanma.

[RANDPS](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id509066?audience=external) · [TABRND1](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id509351?audience=external) · [Power Spectral Density Factors](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1395303?audience=external)

### Bileşen temsili ve external superelement

- Seçim ölçütleri arayüz DOF ve koordinatları, hedef bant, recovery kapsamı, fiziksel state, ölçümden gelen veri ve tekrar kullanım olsun. Mode set için mod kütlesi, normalizasyon, damping ve port eşlemesini doğrula. FRF set için transfer matrisi, referans ve hedef kanallar, birim, faz, frekans tabanı ve assembly bağlantısını doğrula. Tam FEM için çözüm ve recovery kapsamını belirle.
- External SE üretimini ve assembly koşusunu iki izlenebilir aşamada kur. Retained boundary DOF, fixed-interface modları, residual vector veya static reduction, recovery ve çıktı formatı belirlenir. Deck’te `EXTSEOUT`, `ASSIGN`/ünite, matris dosyası ve `SEBULK`/`SECONCT` bağlarını doğrula. Eski mutlak yol, eksik matris veya çakışan interface bağı çözüldüğünde koşu başlasın.
- Küçük iki bileşenli fixture’da tam ve indirgenmiş assembly’yi arayüz kuvvet dengesi, mod frekansı/altuzayı, hedef FRF bandı ve gerekiyorsa iç recovery ile kıyasla. Yanlış arayüz yönü ve eksik mode coverage durumlarını ayrı test et.

[FRF set in assembly FEM](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1390975?audience=external) · [Edit a mode set or FRF set](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1411480?audience=external) · [EXTSEOUT](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.QRG/html/id509506?audience=external) · [External Superelement Examples](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.super/html/id790054?audience=external)

### NVH kaynak tanımlama, PCA ve TPA

- Bilinen H ve ölçülmüş y ile `Hf ≈ y` sistemini kompleks olarak kur. Kanal, geometri, birim ve çalışma durumu eşleşsin. Rank, singular values, koşul sayısı, ölçeklendirme ve düzenlileştirmeyi frekansa göre incele. Fazladan ölçüm kanallarının gözlenebilirliğe katkısını ölç. Fit residual’ı ve çözümde kullanılmayan bağımsız hedef kanalını doğrula. Doğrudan ölçülmüş yük için ters çözümü atla.
- PCA’da frekans başına Hermit referans CSD’den sanal bileşenleri ve açıklanan gücü çıkar. Faz tutarlılığı, altuzay yakınlığı ve yeniden sentezlenen spektrumun hatasını ölç. Tek bir fiziksel kaynak veya yol atfı için ek deneysel dayanak ara.
- TPA’da yönteme uygun fiziksel girdiyle `cᵢ = Hᵢfᵢ` katkılarını kompleks hesapla. Fazı tutarlı yolları kompleks birleştir. Korelasyonlu güç raporunda çapraz terimleri koru. Önce bağımsız hedefi yeniden üret, sonra yol sıralamasını raporla. Neredeyse tekil H ve faz iptali regresyonlarını kullan. Sıralamayla birlikte bant ve çalışma durumunu kaydet.

[Load identification](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1685198?audience=external) · [Principal component analysis](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1929445?audience=external) · [Transfer path analysis scenario](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1396524-1?audience=external)

## 4. Araç ve uygulama sözleşmesi

| İhtiyaç | İlk seçim | Gözlem sınırı ve fallback |
| --- | --- | --- |
| Part, mesh, malzeme ve BC envanteri | Simcenter 3D Model Inspection. Assembly, solution/subcase veya ileri CAE nesneleri için kapsamı doğrulanmış salt okunur NXOpen yolu. | Güncel profil kataloğundan şemayı al. Bağlantı durumunun ardından işlemin kendi readback’ini al. |
| Response Dynamics olayı, mode/FRF set, RANDPS modeling object | Designcenter Open ve hedef sınıf/sürüm. Native okuma ve yazım için ayrı operasyon kayıtları. | `Simulation.ResponseSimulationManager.EvaluationSettingManager` gözlenen yol. `getattr` vendor sandbox tarafından reddedildi. Açık üye erişimi çalıştı. Kurulu .NET dokümanındaki `ToArray()` çağrısı ilgili Python koleksiyonlarında bulunmadı. 2612 batch Python oturumunda doğrudan iterasyonla event ve excitation nesneleri okundu. |
| Solver kanıtı | Varsa Nastran diagnostic MCP, ardından yetkili deck/F06 metni. Çözüm koşusu için [Solution Sequence](../skills/fea-solver-investigation/references/solution-sequence.md). | Dosyayı ve state’i sabitle. Lexical kart gözlemi, çözümlenen aktif setler, solver tamamlanması ve mühendislik kabulü ayrı çıktılar. INCLUDE, continuation ve ASSIGN referanslarını yetki kapsamı içinde çöz. |
| Alan sonucu ve export | İzole BatchPost worker ve güncel sonuç şeması. | Open/list/export ayrı aşamalar. Boş katalogda F06 ve native result reference ile kimliği doğrula. Fonksiyon, response-event veya matris için uygun okuyucuda dar keşif yap. Desteklenmeyen alanı raporla. |
| Siemens bilgi kaynağı | Siemens Help Server, ilgili ürün ve gerçek hedef release ile. | Dönen başlık ve sürümü kontrol et. UI ve .NET örneği için Python üyelerini doğrula. Yeni descriptor/builder için dar read, gerekiyorsa sentetik etki ve persist/reopen. |

İşlem kaydı `intent, owner, profile, runtime_build, requested_doc_version, resolved_doc_version, member_or_schema, scope, preconditions, witness, evidence_status, fallback` taşır. Yazımda [native runtime gate](../skills/fea-native-runtime-gate/SKILL.md) ile bağımsız sentetik hedef, oturum/owner bağı, yeni yol, önce/sonra okuma ve yeni oturumda reopen kullanılır. Etki belirsizse yeni readback alınır. Salt okunur tip erişimi gelecekteki mutasyon yeteneğini açık bırakır.

[NXOpen Python ResponseSimulation.Manager](https://docs.sw.siemens.com/documentation/external/PL20251024323638784/en-US/custom_api/nxopen_python_ref/a50173.html) · [EvaluationSettingManager](https://docs.sw.siemens.com/documentation/external/PL20251024323638784/en-US/custom_api/nxopen_python_ref/a50081.html)

## 5. Skill değişiklikleri ve PR sırası

39 giriş noktası başlangıç yapısı olarak korunur. Her root kısa tetikleyici ve ilk karar için gereken bilgiyi taşır. Formül, solver kartı, yazım prosedürü ve kabul testleri gerektiğinde okunur. Eğitimdeki konuşma dilini teknik ölçütlerle değiştir. Her değişiklik kaydında mevcut kaynak, karar, hedef, teknik kanıt ve beklenen regresyon olsun. Ayrı NVH skill’i ancak held-out prompt testinde mevcut `fea-dynamics` yapısı kalıcı yanlış rotaya neden olursa değerlendir.

Mevcut `fea-dynamics/references/advanced-dynamics.md` içindeki SRS kararını yeni SRS referansına taşı ve eski bağlantıyı koru. `fea-random-response/references/engineering-method.md` spektral matematiğin, `fea-modal-correlation/references/engineering-method.md` mod eşlemenin kaynağı olarak kalır. Yeni referanslar bu kuralları kullanır ve kendi solver/işlem kararını ekler. Üç kanala dağıtılan root, talimat ve örnek içerikleri aynı kanonik kaynaktan üretilir.

| Sıra | Değişiklik | Dosyalar ve kabul |
| --- | --- | --- |
| 1 · Routing ve kanıt | **KEEP** profil, yetki ve readback. **NARROW** fiziksel niyet, operasyon ve araç kararı. **RELOCATE** API ve format ayrıntıları. **REMOVE** demo adları, label/ID, mutlak path, konuşma metni ve sabit demo parametreleri. | `fea-chief-engineer`, `fea-sc3d-tool-routing/SKILL.md` ve `references/tool-matrix.md`, `fea-dynamics/SKILL.md`, `docs/skill-catalog.md`. Doğru yöntem, uygun araç ve gereksiz discovery’yi önleyen route eval. |
| 2 · Deck ve sonuç kapsamı | Mevcut SOL 101/103 checker’ı ve fail-closed davranışını koru. İleri incelemeye ayrı gözlem modu tasarla. `SDAMPING`, `RANDOM`, `METHOD` qualifier, `SET … THRU …` continuation ve executive `ASSIGN` sentetik girdilerle sınansın. Kartın yeri ve çözülemeyen referans dönsün. | `simcenter-nastran/scripts/deck.py`, `references/deck-and-solutions.md`, `tests/test_nastran_deck.py`, `fea-artifact-forensics`, `fea-solver-investigation`, `batchpost-actions`. Eski fixture’lar geçer. Boş veya desteklenmeyen katalog yanlış kabul üretmez. |
| 3 · Dinamik yöntemler | SRS/Response Dynamics ve forced response için dar referanslar. Random teorisini koru, Nastran akışını ayrı referansa ekle. Modal damping projeksiyonu, ölçümden damping fit ve mode-set readback’i bağla. | `fea-dynamics/references/`, `fea-random-response/references/`, `fea-modal-correlation`, `designcenter-open-journal-authoring/references/cae-2612.md`. Bağımsız sentetik sayı ve her sınanmış NXOpen üyesi ya da solver yoluna sürüm/kapsam kaydı. |
| 4 · Bileşen ve NVH | Tam FEM/mode set/FRF set/external SE seçim referansı. Load identification, PCA ve TPA için ayrı görev referansları. Girdi, yöntem, operasyon ve sonucu aynı fixture üzerinden izle. | `fea-model-preparation/references/`, `fea-dynamics/references/`, gerektiğinde `fea-results-interpretation` ve `fea-acceptance-verifier`. Full-vs-reduced, held-out rekonstrüksiyon, yanlış port/frame, rank ve faz iptali testleri. |
| 5 · Aday ve host yeterliliği | AgentsAI, Codex ve VS Code’a tek kanonik kaynaktan dağıt. Release kanıtına doğrulanan kapsamı ve açık operasyonları yaz. | `plugin.json`, `.sim-ai-agents.toml`, mevcut kurulum/marketplace kanalları ve `scripts/package_release.py`. Windows/Linux CI, paket parity, üç istemcide taze chat ve capability kaydı. |

Üçüncü PR için referans adayları `response-spectrum.md`, `forced-response.md`, `modal-damping.md` ve random skill altında `nastran-random-response.md`. Dördüncü PR için `component-representations.md`, `external-superelements.md` ve soru türüne göre açılan `nvh-load-identification.md`, `nvh-principal-components.md`, `nvh-transfer-paths.md`. Her referans kendi girdi, çıktı ve durma koşullarını taşır. Ortak formüller ve doğrulanmış API kanıtı kaynak dosyalarında kalır.

[Rethinking skills and prompts for GPT‑6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) · [Agent Plugins 1.0 şeması](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)

## 6. Test matrisi, dağıtım ve çıkış ölçütleri

1. **Route eval.** Her yeni yönteme bir doğrudan talep, bir günlük dilde talep ve komşu rotaya girmesi gereken zor negatif. Held-out setinde SRS/PSD/transient, SOL 111 deterministik/random, inverse load/PCA/TPA, FRF set/external SE ve boş katalog senaryoları olsun. Birincil skill, destek referansı, ilk araç ve kanıt seviyesi ölçülür. Kritik rotalarda sıfır yanlış kabul ve izinsiz mutasyon hedeflenir. Temel 39 skill’in keşfi, açılan referans sayısı, ilk yararlı çağrıya kadar adım ve bağlam büyüklüğü önce/sonra karşılaştırılır.
2. **Offline test.** Sentetik fixture’lar bağımsız hesap, birim ve önceden tanımlanmış mutlak/bağıl tolerans taşır. Deck testlerinde 101/103, ileri kayıtlar, include/assign, yanlış etkin set ve bilinmeyen kart sınanır. Paketleri eğitim varlığı, `.work`, kayıtlı journal, mutlak kaynak yolu ve eğitim sonuç dosyası sızıntısı için denetle.
3. **Lisanslı 2612 test.** İlk geçişte bağımsız PRT/FEM/SIM save/reopen, SOL 108/111 deterministik, SOL 111 random ve SRS event etkisi. Sonraki geçişte eşdeğer modal damping, haricî SE assembly ve NVH fonksiyon/sonuç okuyucusu. Kimlik, şema, build, lisans, hash, QoI ve tolerans kaydedilir. Gerekli API veya lisans erişilemiyorsa etkilenen operasyon `NOT_RUN` veya `UNVERIFIED` kalır.
4. **Dağıtım.** [Source validation](../.github/workflows/validate.yml) ile Windows ve Linux testleri, manifest, link closure ve deterministik paket. Tek `skills/` ağacından dağıtım ve proje kurulumları. Kanal/aday digest’i, canonical skill parity, idempotent install, upgrade ve rollback doğrulanır.
5. **İstemci kabulü.** AgentsAI’de auth’lu taze chat ve bundle discovery. Codex’te portable install ve taze app-server/desktop chat, doğru profil ve readback. VS Code’da gerçek Copilot extension chat ve project custom-agent tool allowlist, ayrı portable-only ajan seçimi. 0.1.6’da AgentsAI taze chat auth’ta durdu. Copilot CLI’da portable skill keşfi ve proje ajanı çalıştı, portable-only özel ajan seçimi başarısızdı. Üç istemcide aynı sentetik SOL 111 routing ve boş katalog vakası çalıştırılır. [0.1.6 kanal kanıtı](qualification/0.1.6.md)
6. **Yayın kabulü.** Her yöntem için kaynak kapsamı, native read/effect, persisted/reopened, solver ve bağımsız engineering acceptance kaydı tutulur. PR’lar bağımlılık sırasıyla birleştirilir. Yöntem kaynak olarak yayımlanabilir. Otomatik ileri işlemler için ilgili host ve yöntem yeterliliği gerekir.
