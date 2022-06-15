# Channel Modifiers

## Linear Blend

A python channel modifier version from the SDK samples cmLinearBlend

### Config

To make plug-ins more user friendly, Modo expects us to define plenty of things through config files.

#### Command Help

Starting off making a command help to make nicer names for the channels and the modifier item itself. This should allow for localization also so someone else could add a Command Help in different language.

``` xml
<atom type="CommandHelp">
    <hash type="Item" key="py.chanmod.linearblend@en_US">
        <atom type="UserName">Linear Blend</atom>
        <hash type="Channel" key="inputA">
            <atom type="UserName">Input A</atom>
            <atom type="Desc">First input to blend</atom>
        </hash>
        <hash type="Channel" key="inputB">
            <atom type="UserName">Input B</atom>
            <atom type="Desc">Second input to blend</atom>
        </hash>
        <hash type="Channel" key="blend">
            <atom type="UserName">Blend Amount</atom>
            <atom type="Desc">Zero blends fully to Input A while 100% goes fully to B</atom>
        </hash>
        <hash type="Channel" key="output">
            <atom type="UserName">Output</atom>
            <atom type="Desc">The resulting value of blending between A and B</atom>
        </hash>
    </hash>
</atom>
```

Here we tell Modo that the item `py.chanmod.linearblend` will have the user name "Linear Blend" with the english localization. Then under this item we define a nice name for the channels and add a `Desc` which will act as tooltip whenever users hoovers over the channels in UI.

#### Property Panel

Here we will be using two groups to work together, a `filterPreset`  and a `sheet` - the sheet will be the displayed UI and we will put it in the item property. The filter will be used so that it only displays when users have the channel modifier selected.

```xml
<atom type="Filters">
    <hash type="Preset" key="py.chanmod.linearblend:filterPreset">
        <atom type="Name">Linear Blend</atom>
        <atom type="Description"></atom>
        <atom type="Category">ProceduralItem:filterCat</atom>
        <atom type="Enable">1</atom>
        <list type="Node">1 .group 0 &quot;&quot;</list>
        <list type="Node">1 itemtype 0 1 &quot;py.chanmod.linearblend&quot;</list>
        <list type="Node">-1 .endgroup </list>
    </hash>
</atom>

<atom type="Attributes">
    <hash type="Sheet" key="py.chanmod.linearblend:sheet">
        <atom type="Label">Linear Blend</atom>
        <atom type="Filter">py.chanmod.linearblend:filterPreset</atom>

        <hash type="InCategory" key="itemprops:general#head">
            <atom type="Ordinal">128</atom>
        </hash>

        <!-- Makes a collapsible group -->
        <list type="Control" val="div ">
            <atom type="Label">Linear Blend</atom>
            <atom type="Alignment">full</atom>
        </list>

        <!-- Add commands to UI to expose channels to users inside this sheet, -->
        <list type="Control" val="cmd item.channel py.chanmod.linearblend$inputA ?"/>
        <list type="Control" val="cmd item.channel py.chanmod.linearblend$inputB ?"/>
        <list type="Control" val="cmd item.channel py.chanmod.linearblend$blend ?"/>
    </hash>
</atom>
```

#### Making a new category

Lastly we will add the channel modifier to a new category, to make it easier to find and not get mixed up with the existing Linear Blend channel modifier residing in the category `others`

``` xml
<atom type="Categories">
    <hash type="Category" key="ChannelModifiers">
        <hash type="C" key="py.chanmod.linearblend">python</hash>
    </hash>
</atom>
```

See full config for linear blend [here](../../configs/chanmod_linearblend.cfg)
