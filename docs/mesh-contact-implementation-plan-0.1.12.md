# FEA Expert 0.1.12 mesh ve temas uygulama planı

## Hedef ve kapsam

Designcenter 2612’de fiziksel bir bölgenin Selection Recipe’den yerel Mesh Control’e, oluşan elemanlara ve solver sonucuna kadar izlenebildiğini kanıtla. SOL 401 ve 402’de mesh çözünürlüğü, yük artımı ve temas kontrolü etkilerini ayrı deneylerle ölç. Doğrulanan yöntemleri üç istemcinin kullandığı ortak skill ağacına aktar.

0.1.11’de ilişkisel CAD–FEM remesh ve 2B SOL 401 cıvata önyükü ve temas sonuçları doğrulandı. 0.1.12’nin yeni kanıtı kalıcı seçim tarifi, yerel mesh kontrolünün ölçülebilir etkisi, bölgesel kalite kontrolü ve üç boyutlu temasın yakınsaması. Help Server, 2612 isteğinde ilgili kılavuzları çoğunlukla 2606 olarak döndürüyor. Kurulu build’deki API davranışı ayrı canlı kanıt gerektiriyor. [0.1.11 kalifikasyonu](qualification/0.1.11.md)

| Sıra | İş paketi | Geçiş ölçütü |
|---|---|---|
| 1 | Canlı 2612 bağlantısı ve API keşfi | Aynı oturuma bağlı profiller, sahip nesneler, çağrı yüzeyi ve okuma yolu belirlendi. |
| 2 | Seçim, kontrol ve kalite zinciri | Boyut değişimi, yüz bölünmesi ve reopen sonrası fiziksel seçim, yerel boyut ve kalite kanıtlandı. |
| 3 | Üç boyutlu Hertz | 401 ve 402’de üç mesh seviyesi ve üç yük durumu bağımsız analitik referansla karşılaştırıldı. |
| 4 | Temas yakınsaması | İki çözücüde kapanma ve yeniden açılma doğrulandı. Artım, mesh ve temas sertliği etkileri ayrı ölçüldü. |
| 5 | Skill ve dağıtım | Canlı kanıt, ortak skill içeriği, üç istemci paketi ve Windows/Linux CI aynı adaya bağlandı. |

## 1. Canlı 2612 oturumu ve API keşfi

1. Kurulu build’i ve işlem kimliğini ölç. Designcenter Open ve Simcenter 3D Model Inspection profillerini aynı oturuma bağla. Açık parça envanteri, work/display ve değişiklik durumunu kaydet. Test için ayrı isimli, göreve ait PRT/FEM/SIM zinciri kullan.
2. Kurulu NXOpen stub’ları, Help ve gerekirse küçük bir UI journal kaydıyla üç işlemi keşfet. Selection Recipe oluşturma ve üyelerini çözme, Mesh Control oluşturma ve hedefini okuma, Element Quality kapsamı ve hata gruplarını alma. Her işlem için sahip nesne, üye, parametre, beklenen etki ve bağımsız okuma yolunu kaydet.
3. Canlı MCP’de her yazımdan sonra modeli yeni bir çağrıyla oku. Üye çözümlemesi, kontrolün bağlanması, remesh ve kalite ayrı gözlemlerdir. Belirsiz sonuçta yeni etki göndermeden önce canlı durumu tekrar ölç.
4. Test dosyalarını izole run_journal.exe ile kaydet. Taze süreçte reopen ve dosya SHA-256 kontrolü yap. Ardından aynı dosyaları canlı oturumda açıp CAD/FEM/SIM ilişkisini, seçim üyelerini, mesh kontrolünü ve çözülebilen sonuç referansını bağımsız oku. Batch ve canlı icra aynı parametrelerle yapıldığında gözlenen sonuçları kıyasla. Test ağacını kapatınca başlangıç rollerini doğrula.

[Native persistence](../skills/fea-native-runtime-gate/references/native-persistence.md) · [2612 CAE operasyonları](../skills/designcenter-open-journal-authoring/references/cae-2612.md)

## 2. Selection Recipe → Mesh Control → mesh quality

### Seçimi doğrula

Fillet, silindirik yüz, ince kesit ve birbirine yakın ama farklı görevli yüzler içeren küçük bir CAD/FEM/SIM üret. Temasın iki tarafını, yük yüzünü ve desteği ayrı tariflerle temsil et.

- Tarifi fiziksel rol, sahip gövde ve occurrence, koordinat sistemi, yüzey tipi, konum, normal ve beklenen alanla sınırla. Aynı adı taşıyan veya yakında duran bir yüzle yanlış seçim kontrolü yap.
- Başlangıçta, boyut değişiminde, bir fiziksel yüz ikiye bölündüğünde ve kaydedilmiş model yeniden açıldığında üyeleri oku. CAD boyut değişikliğinde yeni beklenen alanı hesapla. Yüz bölünmesinde çocuk yüzlerin toplam alanı ve kapsaması önceki fiziksel rolle tutarlı kalmalı. Boş, fazla geniş veya yanlış occurrence’a çözülen seçim durumu hata vermeli.
- İlk sentetik modelde geometri alanı için %1 fark ve beklenen taraftaki normal yönünü kabul ölçütü olarak kullan. Dışlanacak yüzlerle örtüşme sıfır olmalı. Reopen sonrasında fiziksel üyelik ve kontrolün etkisi aynı ölçümle karşılaştırılır.
- Doğrudan Selection Recipe bağlanabiliyorsa kalıcı ilişkiyi ve remesh sonrasındaki üyeleri doğrula. Kontrol somut entity bekliyorsa her güncellemede tarifi yeniden çöz ve kontrol hedefini güncelle. İki davranışı ayrı kaydet. Çakışan kontroller ve Bounding Volume taşımasını küçük bir örnekte ölç. PL8004062 başlık düzeyinde bir keşif girdisi.

[Selection Recipes](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid1314328?audience=external) · [Boolean Selection Recipes](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/ycf5429854366160?audience=external) · [PL8004062](https://support.sw.siemens.com/en-US/knowledge-base/PL8004062)

### Kontrolün gerçekleşen etkisini ölç

| Bölge | Denenecek kontrol | Ölçüm |
|---|---|---|
| Temas izi ve kenarı | İki yüz için Size on Face ve kaba mesh’e geçiş bandı | Gerçek kenar boyu dağılımı, temas genişliği başına facet sayısı ve yüz normalleri |
| Fillet ve silindir | Eğrilik, chordal tolerance veya uygun fillet/cylinder kontrolü | Yüzey yaklaşım hatası, midside node konumu ve Jacobian kontrolü |
| İnce kesit ve geçiş | Edge divisions, edge size veya bias. Uygun gövdede sweep adayını karşılaştır. | Kalınlık doğrultusu, karşı kenar uyumu ve geçişte düşük kaliteli elemanların konumu |

Otomatik baseline ile yerel kontrollü mesh’i aynı eleman ailesi ve mertebesinde karşılaştır. Kontrole girilen nominal boyutu, iki tarafta gerçekleşen yerel boyutu, kalite dağılımını ve toplam serbestlik derecesini ayrı kaydet. Karşılaştırma bölgesi, seçimin CAD ve FEM üzerindeki kanıtıyla aynı olmalı. [Siemens Mesh Controls](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.design/html/id628236?audience=external)

### Bölgesel mesh kalitesini doğrula

- mesh-info-tool ile mesh, collector, eleman tipi, mertebesi ve sayısını doğrula. mesh-quality-tool ile mevcut kapsamı tara. Kritik yüzün komşu elemanları için native Element Quality veya canlı doğrulanmış NXOpen eşdeğerini kullan. Uyarı ve hata eşiği, ölçülen eleman sayısı, problemli elemanlar ve fiziksel bölgeyi kaydet.
- Connectivity, beklenmeyen serbest kenar, çökme ve ters elemanları incele. Tet10’da midside node konumunu ve solver’ın örnekleme noktalarındaki Jacobian kontrolünü doğrula. Düşük kaliteli bir örneğin işaretlenmesini ve düzeltme sonrası aynı bölgedeki değişimi ölç. Sıfır eleman değerlendiren veya gerekli metriği sağlamayan çıktı UNVERIFIED olarak kalır.

[Native Element Quality](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/id630491?audience=external) · [Nastran kalite kontrolleri](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid452984?audience=external) · [Sandia yüksek mertebe metrikleri](https://cubit.sandia.gov/files/cubit/17.08/help_manual/WebHelp/mesh_generation/mesh_quality_assessment/higher_order_metrics.htm)

## 3. Hertz benchmark

### Geometri ve bağımsız hesap

Sürtünmesiz, lineer elastik bir küreyi elastik düz bloğa bastır. Önerilen sentetik başlangıç değerleri R = 50 mm, her iki gövdede E = 70 000 MPa ve ν = 0,30. Temasın uzağından eksenel yük aktar. Başlangıç gap’i ve normal yönünü ölç. Bloğun uzak sınırlarını büyüterek sonuç hassasiyetini kontrol et. Çeyrek simetri kullanılırsa yükü, reaksiyonu ve temas alanını tam model ölçeğine getir. Referans elastik yarı uzay yaklaşımı, küçük temas izi ve küçük deformasyon varsayar.

Tam model için E* = [(1−ν₁²)/E₁ + (1−ν₂²)/E₂]⁻¹ ve R* = R. Analitik temas yarıçapı a = [3 F R* / (4 E*)]^(1/3), merkez basıncı p₀ = 3F/(2πa²), bağıl yaklaşma δ = a²/R* ve radyal basınç p(r) = p₀√(1−(r/a)²). Referans sayıları solver sonuçlarından bağımsız hesapla.

| Tam model yükü | Temas yarıçapı | Merkez basıncı | Bağıl yaklaşma |
|---:|---:|---:|---:|
| 25 N | 0,289945 mm | 141,988 MPa | 0,00168136 mm |
| 50 N | 0,365307 mm | 178,894 MPa | 0,00266899 mm |
| 100 N | 0,460258 mm | 225,392 MPa | 0,00423675 mm |

[Küre ve elastik düzlem için Hertz formülleri](https://arpi.unipi.it/retrieve/5aa38bf2-7cbd-41ac-a710-68531c1422fc/lubricants-10-00233-v2.pdf) · [Hertz temas doğrulama yöntemi](https://docs.software.vt.edu/abaqusv2026/English/SIMACAEBMKRefMap/simabmk-c-hertzcontact.htm)

### Çözüm matrisi ve kabul ölçütleri

1. Aynı geometri ve malzemeyle SOL 401 ve 402 için üç mesh seviyesi çöz. İlk yerel boyut adayları 100 N temas yarıçapına göre a/4, a/8 ve a/16. Gerçekleşen boyutları iki temas yüzünde ölç. İnce mesh’in 25 N temas izini de yeterince örneklediğini kontrol et. Her iki solver’da aynı fiziksel yüklerde kabul edilmiş durumu kıyasla.
2. Temas yarıçapını aktif alan üzerinden √(A/π) ile çıkar ve temas kenarıyla karşılaştır. Kısmen aktif facet’lerin alan ölçümüne etkisini kaydet. Merkez basıncını aynı recovery yöntemiyle ölç. Basınç profilini aynı radyal konumlarda, aynı tarafta karşılaştır. Uygulanan kuvvet, destek reaksiyonu, bir taraftaki temas resultants ve mevcutsa basınç integrali arasında dengeyi göster.
3. Bağıl yaklaşmayı iki referans konumundan çıkar. Uzak sınır ve yük aktarım bölgesi uyumluluğunun bu ölçüme etkisini ayrı değerlendir. Önceden seçilen ölçüm yöntemini mesh seviyeleri arasında koru.

| Önerilen fixture kabul ölçütü | Başlangıç hedefi |
|---|---:|
| Uygulanan yük ve destek reaksiyonu arasındaki kuvvet farkı | ≤ %1 |
| Normal temas kuvveti ile uygulanan yük farkı | ≤ %2 |
| 100 N ince mesh’te temas yarıçapı ve merkez basıncı hatası | Her biri ≤ %5 |
| 25 ve 50 N ince mesh’te aynı iki büyüklüğün hatası | Her biri ≤ %8 |
| 100 N orta–ince mesh farkı | Yarıçap ve merkez basıncı için ayrı ayrı ≤ %3 |
| 100 N bağıl yaklaşma ve radyal profil | Yaklaşma hatası ≤ %5. Ortak 0 ≤ r/a ≤ 0,9 örneklerinde profil RMSE’si ≤ 0,05 p₀. Kenar konumu ayrıca raporlanır. |
| 100 N fiziksel temas ölçeğine göre penetrasyon | En büyük gözlenen penetrasyon ≤ 0,10 δ. Ölçüm noktası ve solver’ın normal gap işareti kaydedilir. |
| Uzak sınır büyütmenin etkisi | Son iki boyutta yarıçap ve merkez basıncı farkı ayrı ayrı ≤ %2 |

Bu eşikler fixture için önerilen başlangıç değerleridir. Geometri, ölçüm yöntemi ve toleransları çözümden önce kaydet. Her solver için etkin deck, F06, OP2, BatchPost sayısal çıktı ve analitik karşılaştırma tablosu üret. İnce mesh SIM’lerini canlı 2612’de aç, bağlı FEM ve temas çiftinin yanı sıra aynı OP2 referansını oku. Native sonuç erişiminin sağladığı en az bir sayısal büyüklüğü aynı OP2’den alınan BatchPost sonucu ve uygun F06 tablosuyla karşılaştır.

## 4. SOL 401 ve 402 temas yakınsaması

### Hertz dışında ayırt edici geçiş deneyi

İki elastik blok ve bilinen ilk açıklığa sahip deplasman kontrollü bir model kullan. Sürtünmesiz, düzgün eksenel bası ve yanal serbestlik varsayımında kapanma d = g₀’da olur. Kapalı yöndeki kuvvet F = max(0, d−g₀) / [L₁/(E₁A) + L₂/(E₂A)]. Yük programı temasa yaklaşma, kapanma, kapalı durum ve geri açılmayı kapsasın.

Önerilen sentetik başlangıç her blok için L = 10 mm, A = 100 mm², E = 2 000 MPa ve ν = 0, ilk açıklık için g₀ = 0,05 mm. Normal yönde hareketi üst yüzeye uygula ve alt yüzeyi destekle. Yanal rijit cisim hareketini fiziksel uyumluluğu değiştirmeyecek şekilde sınırla. Tam modelde d = 0,025 mm’de açık temas ve 0 N, d = 0,075 mm’de 250 N, d = 0,100 mm’de 500 N beklenir. Boşaltmada 0,025 mm’ye dönüldüğünde açık temas ve 0 N yeniden gözlenmeli.

- Temas öncesi pozitif açıklığı ve tolerans içinde sıfır kuvveti ölç. Son açık ve ilk kapalı artım kapanmayı sınırlandırmalı. Kapalı durumda normal resultants ve destek reaksiyonu seri uyumluluk referansıyla eşleşmeli. Geri açılmada temas kuvveti sıfıra dönmeli ve pozitif açıklık görülmeli. Önerilen ilk eşikler açık durumda mutlak kuvvet ≤ 1 N, kapanma sınırında en fazla bir ince artım ve kapalı durum kuvvetinde ≤ %5 hata.
- Aynı fiziksel durumda üç ayrı duyarlılık deneyi yap. Sabit mesh ve temas ayarıyla artım inceltme, sabit yük programıyla yerel mesh inceltme, sabit mesh ve artımla temas sertliği değişikliği. Otomatik penalty ölçeklemesi mesh’le değişiyorsa solver’ın gerçekleşen değerini kaydet. Penetrasyonu yerel mesh boyuna ve fiziksel açıklık veya yaklaşma ölçeğine göre raporla.
- Bir çift eşleşme hatasını negatif kontrol olarak kullan. Yanlış occurrence veya yüz kapsamı mesh ve solve öncesinde bölge okumasında görünmeli. Aynı modelde kaba artım yorumu için uygun bir reddedilmiş artım, cutback veya bisection örneği elde edilebilirse son kabul edilen fiziksel durumu da kaydet. Bu tanı senaryosunun kapsamı gerçekleşen solver çıktısına göre raporlanır.
- Önyük ve kilitleme geçmişi için 0.1.11 cıvata testini regresyon olarak kullan. Ayrı bir genişletme deneyinde normal yükü sabitleyip teğetsel yükü artırarak stick/slip ve μFₙ sınırını değerlendir.

### Solver’a özgü tanı ve canlı okuma

| Solver | Etkin input ve tanı | Ölçülecek durum |
|---|---|---|
| **SOL 401** | Aktif BCSET ve BCTSET zincirini, BCTPARM, NLCNTL ve TSTEP1 seçimlerini çöz. F06’da Newton denge döngüsünü ve temas augmentasyonunu, EQU, CON, varsa BLT, bisection ve ulaşılan durumu ayrı oku. Kurulu sürümde uygulanabilir PTOL/CTOL ve ilgili çıktı ayarlarını doğrula. | Son kabul edilen yük, çift kuvveti, açıklık veya penetrasyon ve reaksiyon dengesi. Solver’ın kabul ölçütüyle fiziksel kabulü ayrı kaydet. |
| **SOL 402** | Aktif çift, subcase etkinliği ve bağımlılığı, BCTSET, BCTPAR2, NLCNTL2 ve zaman programını çöz. MSGLVLC ile çift kuvveti, normal mesafe ve açık/temasta durumu al. REDUNDANT kayıtlarını ilgili kısıt veya glue çiftine bağla. | Son kabul edilen kuvvet ve deplasman, açıklık, aktif alan ve kuvvet dengesi. Geri açılan bölgeleri önceki kabul durumlarıyla fiziksel konum üzerinden karşılaştır. |

İlk gap, ters normal, serbest cisim hareketi ve çakışan kısıtlar için preflight kontrolü yap. Canlı 2612’de kapanma ve açılma modelini yeniden aç. Etkin çift, subcase, bağlı FEM ve OP2 kimliğini doğrula. Aynı durumun solver tanısını F06’dan, gap, status, basınç ve kuvvetini OP2’den al. Stabilizasyon tercih edilirse mühendislik ölçülerine ve ilgili enerji veya iş göstergelerine etkisini karşılaştır.

[SOL 401 yakınsama](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid1201098?audience=external) · [SOL 401 temas tanı çıktısı](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2056291?audience=external) · [SOL 402 temas tanısı](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2016266?audience=external) · [SOL 402 ilk gap ve TIED](https://support.sw.siemens.com/en-US/knowledge-base/KB000206445_EN_US) · [SOL 402 glue ve ilk gap](https://support.sw.siemens.com/en-US/knowledge-base/KB000207992_EN_US)

### Denemeleri ve kanıtı bağlama

| İş | Her solver için asgari çalışma | Sabit tutulanlar |
|---|---|---|
| Hertz serisi | Kaba, orta ve ince. Uzak sınır kontrolü için ince mesh’in ikinci alan boyutu. | Temas tanımı, eleman formülasyonu, malzeme, yük noktaları ve recovery |
| Açık–kapalı–açık temas | Baseline, küçük artım, yerel ince mesh ve tek temas sertliği değişikliği | Her karşılaştırmada yalnızca ilgili değişken farklı. Aynı fiziksel deplasmanlardaki durumlar eşlenir. |
| Canlı doğrulama | İnce Hertz ve geçiş modeli üzerinde ayrı reopen. Bölge, etkin subcase ve bağlı sonuç okunur. | SIM/FEM ve OP2 kimliği solver ve sonuç karşılaştırmasıyla eşleşir. |

Otomatik çözüm adımı hedeflenen yük veya deplasman noktasını atlıyorsa, ölçüm için o noktada bir sonuç durumu üretecek yük programı kullan. Kontak durumunun değiştiği iki artım arasında interpolasyon yaparak açılma veya kapanma kanıtı oluşturma.

## 5. Skill, paket ve teslim

| Mevcut skill veya grup | Planlanan değişiklik |
|---|---|
| simcenter-3d-mesh-generation ve designcenter-open-journal-authoring | Canlı doğrulanan Selection Recipe ve Mesh Control üyeleri, sahiplik, güncelleme ve bağımsız readback. |
| fea-open-meshing, fea-mesh-quality ve simcenter-3d-mesh-quality-review | Fiziksel bölgeden eleman ailesi ve yerel kontrole geçiş. Collector taramasından kritik yüz ve hatalı eleman kapsamına iniş. |
| fea-connector-contact, fea-multistep-nonlinear ve simcenter-nastran | Ortak temas fiziği, solver’a özgü tanı, etkin deck, ulaşılan artım ve sayısal kontrol. |
| fea-sc3d-tool-routing | Mesh üretimi, kalite kusuru, mesh yakınsaması ve temas çözümü için doğru girişe yönlendirme. Üç istemcide ortak rota. |

Sentetik geometri, solver deck ve referans değerleri fixture ve kalifikasyon kaydında tutulur. Skill’ler fiziksel yöntemleri, sürüm kapsamını ve ölçüm akışını taşır. Analitik ve solver karşılaştırmalarını mevcut fixture doğrulama düzenine bağla. Yerel dosya yollarını, model etiketlerini ve test verilerini paketlenen skill metinlerine taşıma.

1. Her deney için host build, model ve mesh revizyonu, seçim ve kontrol kanıtı, dosya ve deck hash’i, solver/job kimliği, kabul edilen durum, F06/OP2 ve bağımsız ölçümü bağla. Kalifikasyon tablosunda gözlem, tolerans, araç ve durum birlikte yer alsın.
2. docs/qualification/0.1.12.md içinde canlı zincir, Hertz 401, Hertz 402, temas teşhisi 401 ve temas teşhisi 402 için ayrı sonuç kaydet. Ölçülmemiş özellik UNVERIFIED, çalıştırılmamış deney NOT_RUN olarak kalır.
3. Yerel testleri, dağıtım doğrulamasını ve paket üretimini çalıştır. AgentsAI’yi izole katalogda etkinleştir, Codex ve VS Code paketlerini temiz projelerde kur. Üç manifest, sürüm kimliği ve ortak skill içeriklerini karşılaştır.
4. PR’da Windows ve Linux CI’nin aynı commit üzerinde geçtiğini doğrula. Runner arşivlerinin içeriğini ve kaynak kimliğini yerel adayla karşılaştır. Canlı kabul ve paket kanıtları aynı sürüm adayına bağlandıktan sonra PR’ı main’e birleştir.

[Dağıtım doğrulaması](../scripts/validate_distribution.py) · [Windows/Linux CI](../.github/workflows/validate.yml)
